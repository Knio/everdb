# pylint: disable=W0311

import array
import zlib

from .blockdevice import BlockDeviceInterface
from .header import Header, Field

BLOCK_BITS = (12) # 4096 bytes
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

# ammount of space to use in the index
# for single-level block pointers
ONE_LEVEL  = (INDEX_SIZE >> 1)

# logical page number and offset
BLOCK  = lambda x:(x >> BLOCK_BITS)
OFFSET = lambda x:(x &  BLOCK_MASK)

# block pointer to indexes into blob header / page block
# for multi level page tables
INDEX0 = lambda x:ONE_LEVEL + (((x - ONE_LEVEL) >> INDEX_BITS) & INDEX_MASK)
INDEX1 = lambda x:((x - ONE_LEVEL)               & INDEX_MASK)

ZERO_BLOCK = b'\0' * BLOCK_SIZE

SMALL_BLOB = 1
REGULAR_BLOB = 2


class Blob(BlockDeviceInterface, Header):
  length      = Field('Q')
  num_blocks  = Field('I')
  type        = Field('B')

  def __init__(self, host, root, new=False):
    if host.block_size != BLOCK_SIZE: raise ValueError
    self.host = host
    self.root = root

    if new:
      self.init_root()
    else:
      self.load_header(self.host[self.root])

  def __len__(self):
    return self.length

  @property
  def index(self):
    return self.host[self.root].cast('I')\
      [0:INDEX_SIZE - self._header_size]\
      .cast('B').cast('I') # TODO python22668 workaround

  @property
  def data(self):
    return self.read(0, self.length)

  @data.setter
  def set_data(self, data):
    self.resize(len(data))
    self.write(0, data)

  def flush_root(self):
    self.sync_header(self.host[self.root])
    # print('flush, checksum = %d' % self.checksum)
    self.host.flush(self.root)

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK
    self.length = 0
    self.num_blocks = 0
    self.type = SMALL_BLOB
    self.flush_root()

  def flush(self, b=-1):
    if b == -1:
      # TODO keep track of just these blocks
      self.host.flush()
    else:
      self.host.flush(self.get_host_index(b))

  def close(self):
    if not self.host.readonly:
      self.flush()
      self.flush_root()

  def get_blocks(self, offset, length):
    '''
    Returns list of (block, offset, length) ranges.
    blocks are host block ids
    '''
    if not (0 <= offset <= self.length):
      raise ValueError('offset out of bounds (offset: %d, blob length: %d)' % (offset, self.length))
    if not (0 <= offset + length <= self.length):
      raise ValueError('range out of bounds')

    if self.type == SMALL_BLOB:
      return [(self.root, offset, length)]

    ranges = []
    while length:
      b = BLOCK(offset)
      o = OFFSET(offset)
      l = min(length, BLOCK_SIZE - o)
      offset += l
      length -= l
      ranges.append((self.get_host_index(b), o, l))
    return ranges

  def read(self, offset=0, length=None):
    if length is None:
      length = self.length
    r = []
    for b, o, l in self.get_blocks(offset, length):
      r.append(bytes(self.host[b][o:o+l]))
    return b''.join(r)

  def write(self, offset, data):
    i = 0
    for b, o, l in self.get_blocks(offset, len(data)):
      self.host[b][o:o+l] = data[i:i+l]
      i += l
    if self.type == SMALL_BLOB:
      # TODO don't do this
      self.sync_header(self.host[self.root])

  def get_host_index(self, i):
    # translate a local block pointer to a host block pointer
    if self.type != REGULAR_BLOB:
      raise ValueError('not a regular blob, type=%r' % self.type)

    if i >= self.num_blocks:
      raise IndexError('size: %d, i: %d' % (self.num_blocks, i))

    # one level pointer
    if i < ONE_LEVEL:
      return self.index[i]

    # two level pointer
    i0 = INDEX0(i)
    i1 = INDEX1(i)

    # TODO cache this
    b1 = self.index[i0]
    index1 = self.host[b1].cast('I')
    b2 = index1[i1]
    return b2

  def get_block(self, i):
    return self.host.get_block(self.get_host_index(i))

  def allocate(self, num_blocks):
    if not self.type == REGULAR_BLOB:
      raise ValueError('Can only allocate blocks on a REGULAR_BLOB')

    cur_blocks = self.num_blocks
    dirty = set()

    # TODO allocate all required blocks at once here

    # grow and allocate one level data pointers
    while cur_blocks < num_blocks and cur_blocks < ONE_LEVEL:
      b1 = self.host.allocate()
      self.host[b1] = ZERO_BLOCK
      self.index[cur_blocks] = b1
      dirty.add(b1)
      cur_blocks += 1
      self.num_blocks = cur_blocks

    # grow and allocate two level data pointers
    while cur_blocks < num_blocks:
      i0 = INDEX0(cur_blocks)
      i1 = INDEX1(cur_blocks)

      if self.index[i0] == 0:
        # allocate page table block
        b1 = self.host.allocate()
        self.host[b1] = ZERO_BLOCK
        self.index[i0] = b1

      else:
        b1 = self.index[i0]


      # allocate data block
      b2 = self.host.allocate()
      self.host[b2] = ZERO_BLOCK
      dirty.add(b2)

      # TODO: put this in an inner loop so we don't keep loading
      # the same page table

      # add pointer to data block into page table
      page = self.host[b1].cast('I')
      assert page[i1] == 0
      page[i1] = b2
      dirty.add(b1)
      # need to del local variable so that allocate() works
      # in the next iteration
      del page

      cur_blocks += 1
      self.num_blocks = cur_blocks

    # shrink and free two level blocks
    while cur_blocks > num_blocks and cur_blocks > ONE_LEVEL:
      i0 = INDEX0(cur_blocks - 1)
      i1 = INDEX1(cur_blocks - 1)

      b1 = self.index[i0]
      assert b1 != 0
      index = self.host[b1].cast('I')
      b2 = index[i1]

      assert b2 != 0
      index[i1] = 0
      dirty.add(b1)
      # must del if free causes a db resize
      del index
      self.host.free(b2)

      if i1 == 0:
        self.index[i0] = 0
        self.host.free(b1)

      cur_blocks -= 1
      self.num_blocks = cur_blocks

    # shrink one level data blocks
    while cur_blocks > num_blocks:
      i0 = cur_blocks - 1
      b1 = self.index[i0]
      assert b1 != 0
      self.index[i0] = 0
      self.host.free(b1)

      cur_blocks -= 1
      self.num_blocks = cur_blocks

    # cleanup
    for b in dirty:
      self.host.flush(b)

  def resize(self, length):
    '''
    Resizes the blob to a given length, by truntating it or
    extending with zero bytes.
    '''
    # requested size fits in a small block
    # handles both grow and shrink operation
    MAX_SMALL = BLOCK_SIZE - (self._header_size * 4)
    if length <= MAX_SMALL:
      if self.type == REGULAR_BLOB:
        # copy data to root in small block
        data = self.read(0, length)
        # free data + page blocks,
        self.allocate(0)
        self.host[self.root][0:length] = data
      else:
        # already a small block
        # zero fill from requested length,
        # to make sure truncated data is not leaked
        s = slice(length, MAX_SMALL)
        self.host[self.root][s] = ZERO_BLOCK[s]
        # no zero fill when growing, since we assume the block was
        # zeroed either above or on blob creation
      self.type = SMALL_BLOB
      self.length = length
      self.flush_root()
      return

    # requested size requires a regular blob
    num_blocks = BLOCK(length + BLOCK_MASK)
    cur_blocks = self.num_blocks

    if cur_blocks == num_blocks:
      # don't need to allocate or free any blocks
      # zero fill any truncated space
      b = self.get_block(BLOCK(length-1))
      s = slice(OFFSET(length), BLOCK_SIZE)
      b[s] = ZERO_BLOCK[s]
      self.length = length
      self.flush_root()
      return

    data = None
    if self.type == SMALL_BLOB:
      data = self.read()
      self.index[:] = array.array('I', [0] * len(self.index))
      self.type = REGULAR_BLOB
      self.length = 0

    # allocate/free blocks
    self.allocate(num_blocks)

    # still need this because we may have over-allocated
    # if length was not on a page boundary
    self.length = length
    self.flush_root()

    # copy data back from small block expansion
    if data:
      self.write(0, data)


  def __repr__(self):
    return '''<Blob(root=%d, length=%d, num_blocks=%d, type=%d)>''' % \
        (self.root, self.length, self.num_blocks, self.type)
