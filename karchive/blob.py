import zlib

from .blockdevice import BlockDeviceInterface

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
INDEX1 = lambda x:ONE_LEVEL + (((x - ONE_LEVEL))               & INDEX_MASK)

ZERO_BLOCK = b'\0' * BLOCK_SIZE

SMALL_BLOB = 1
REGULAR_BLOB = 2


class Blob(BlockDeviceInterface):
  HEADER = dict((k, i) for i, k in enumerate([
    'length',
    'type',
    'checksum', # must be last
  ]))

  def __init__(self, host, root, new=False):
    if host.block_size != BLOCK_SIZE: raise ValueError
    self.host = host
    self.root = root
    self.header_size = len(self.HEADER)

    if new:
      self.init_root()
    else:
      self.verify_checksum()

  @property
  def num_blocks(self):
      return BLOCK(self.length + BLOCK_MASK)

  @property
  def header(self):
    return self.host[self.root].cast('I')\
      [INDEX_SIZE - self.header_size:INDEX_SIZE]

  @property
  def index(self):
    return self.host[self.root].cast('I')\
      [0:INDEX_SIZE - self.header_size]

  def __getattr__(self, attr):
    if attr not in self.HEADER:
      raise AttributeError(attr)
    i = self.HEADER[attr]
    return self.header[i]

  def __setattr__(self, attr, value):
    if attr not in self.HEADER:
      return object.__setattr__(self, attr, value)
    i = self.HEADER[attr]
    self.header[i] = value

  def size(self):
    return self.length

  def calc_checksum(self, s):
    data = self.host[self.root][s]
    return zlib.crc32(data)

  def verify_checksum(self):
    checksum = self.calc_checksum(s=slice(None))
    if checksum != 558161692:
      raise ValueError('checksum does not match: %d' % checksum)

  def flush_root(self):
    self.checksum = self.calc_checksum(slice(0,-4))
    print('flush, checksum = %d' % self.checksum)
    self.host.flush(self.root)
    self.verify_checksum() # TODO: remove later when stable

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK
    self.length = 0
    self.type = SMALL_BLOB
    self.flush_root()

  def flush(self, block=-1):
    if block == -1:
      # TODO keep track of just these blocks
      self.host.flush()
    else:
      self.host.flush(self.get_host_index(block))

  def close(self):
    if not self.host.readonly:
      self.flush()
      self.flush_root()

  @property
  def data(self):
    return self.read(0, self.length)

  @data.setter
  def set_data(self, data):
    self.resize(len(data))
    self.write(0, data)


  def get_blocks(self, offset, length):
    '''
    Returns list of (block, offset, length) ranges.
    blocks are host block ids
    '''
    if not (0 <= offset <= self.length):
      raise ValueError('offset out of bounds')
    if not (0 <= offset+length <= self.length):
      raise ValueError('range out of bounds')

    if self.type == SMALL_BLOB:
      return [(self.root, offset, length)]

    ranges = []
    while length:
      b = BLOCK(offset)
      o = OFFSET(offset)
      l = min(length, BLOCK_SIZE - o)
      assert l > 0
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
      self.checksum = self.calc_checksum(slice(0,-4))

  def get_host_index(self, i):
    # translate a local block pointer to a host block pointer
    if self.type != REGULAR_BLOB:
      raise ValueError('not a regular blob, type=%r' % self.type)

    if i >= self.num_blocks:
      raise IndexError('size: %d, i: %d' % (len(self), i))

    # one level pointer
    if i < ONE_LEVEL:
      return self.index[i]

    # two level pointer
    i0 = INDEX0(i)
    i1 = INDEX1(i)

    # TODO cache this
    p1 = self.index[i0]
    index1 = self.host[b1].cast('I')
    b2 = index1[i1]
    return b2

  def get_block(self, i):
    return self.host.get_block(self.get_host_index(i))

  def resize(self, length):
    '''
    Resizes the blob to a given length, by truntating it or
    extending with zero bytes.
    '''

    # requested size fits in a small block
    # handles both grow and shrink operation
    MAX_SMALL = BLOCK_SIZE - (self.header_size * 4)
    if length <= MAX_SMALL:
      if self.type == REGULAR_BLOB:
        # free data + page blocks, copy data to root in small block
        raise NotImplementedError()

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

    # requested size requires a regular block
    data = None
    if self.type == SMALL_BLOB:
      data = self.read()
      self.type = REGULAR_BLOB
      self.length = 0

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

    dirty = set()

    # TODO allocate all required blocks at once here

    # grow and allocate one level data pointers
    while cur_blocks < num_blocks and cur_blocks < ONE_LEVEL:
      b1 = self.host.allocate()
      self.host[b1] = ZERO_BLOCK
      self.index[cur_blocks] = b1
      dirty.add(b1)
      cur_blocks += 1
      self.length = cur_blocks * BLOCK_SIZE

    # grow and allocate two level data pointers
    while cur_blocks < num_blocks:
      i0 = INDEX0(cur_blocks)
      i1 = INDEX1(cur_blocks)

      if self.index0[i0] == 0:
        # allocate page table block
        b1 = self.host.allocate()
        print('allocate page: %d' % b1)
        self.host[b1] = ZERO_BLOCK
        self.index0[i0] = b1

      else:
        b1 = self.index0[i0]

      # allocate data block
      b2 = self.host.allocate()
      print('allocate data: %d' % b2)
      self.host[b2] = ZERO_BLOCK
      dirty.add(b2)

      # add pointer to data block into page table
      index1 = self.host[b1].cast('I')
      assert index1[i1] == 0
      index1[i1] = b2
      dirty.add(b1)

      cur_blocks += 1
      self.length = cur_blocks * BLOCK_SIZE

    # shrink and free blocks
    while cur_blocks > num_blocks and cur_blocks > ONE_LEVEL:
      raise NotImplementedError

      i0 = INDEX0(self.num_blocks - 1)
      i1 = INDEX1(self.num_blocks - 1)

      b1 = self.index0[i0]
      index1 = self.host[b1].cast('I')
      b2 = index1[i1]

      assert b2 != 0
      index1[i1] = 0
      dirty.add(b1)
      del index1 # must del if free causes a db resize
      print('b1: %d b2: %d' % (b1, b2))
      self.host.free(b2)
      if i1 == 0:
        self.index0[i0] = 0
        self.host.free(b1)

      self.num_blocks -= 1

    while cur_blocks > num_blocks:
      raise NotImplementedError

    # still need this because we may have over-allocated
    # if length was not on a page boundary
    self.length = length

    # cleanup
    for b in dirty:
      self.host.flush(b)
    self.flush_root()

    # copy data back from small block expansion
    if data:
      self.write(0, data)


  def __repr__(self):
    return '''<Blob(length=%d, type=%d, checksum=%s)>''' % tuple(self.header)
