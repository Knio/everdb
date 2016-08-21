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

SMALL_PAGE = 1
REGULAR_PAGE = 2


class Page(BlockDeviceInterface, Header):
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
    return self.num_blocks

  @property
  def root_block(self):
    return self.host[self.root]

  @property
  def index(self):
    return self.host[self.root][0:-self._header_size & ~4 + 1].cast('I')

  def sync_header(self):
    Header.sync_header(self, self.host[self.root])

  def flush_header(self):
    self.sync_header()
    self.host.flush(self.root)

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK  # do we need to do this?
    self.num_blocks = 0
    self.type = SMALL_PAGE
    self.sync_header()

  def flush(self, b=-1):
    if b == -1:
      # TODO keep track of just these blocks
      self.sync_header()
      self.host.flush()
    else:
      self.host.flush(self.get_host_index(b))

  def close(self):
    if not self.host.readonly:
      self.flush_header()

  def get_host_index(self, i):
    # translate a local block pointer to a host block pointer
    if self.type != REGULAR_PAGE:
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

  def make_small(self):
    if self.type == SMALL_PAGE: return
    if self.num_blocks != 1:
      raise ValueError('Can only convert page with 1 block to a small page')
    data = bytes(self.get_block(0)[0:-self._header_size])
    self.allocate(0)
    self.type = SMALL_PAGE
    self.host[self.root][0:-self._header_size] = data
    self.sync_header()

  def make_regular(self):
    if self.type == REGULAR_PAGE: return
    b = self.host.allocate()
    hs = self._header_size
    self.host[b][0:-hs] = self.host[self.root][0:-hs]
    self.host[b][-hs:] = ZERO_BLOCK[-hs:]
    self.host[self.root] = ZERO_BLOCK
    self.index[0] = b
    self.type = REGULAR_PAGE
    self.num_blocks = 1
    self.sync_header()

  def get_block(self, i):
    return self.host.get_block(self.get_host_index(i))

  def __getitem__(self, i):
    return self.get_block(i)

  def __setitem__(self, i, v):
    self.host[self.get_host_index(i)] = v

  def allocate(self, num_blocks):
    if not self.type == REGULAR_PAGE:
      raise ValueError('Can only allocate blocks on a REGULAR_PAGE')

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
      # requires TODO above so that we don't call allocate()
      # while holding a pointer to the index

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
      page = self.host[b1].cast('I')
      b2 = page[i1]

      assert b2 != 0
      page[i1] = 0
      dirty.add(b1)
      # must del if free causes a db resize
      del page
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
    # for b in dirty:
    #   self.host.flush(b)
    self.sync_header()

  def __repr__(self):
    return '''<Page(root=%d, type=%d, num_blocks=%d)>''' % \
        (self.root, self.type, self.num_blocks)
