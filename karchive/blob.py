import zlib

from .blockdevice import BlockDeviceInterface

BLOCK_BITS = (12) # 4096 bytes
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)
ONE_LEVEL  = (INDEX_SIZE >> 1)

INDEX0 = lambda x:(x >> INDEX_BITS) & INDEX_MASK
INDEX1 = lambda x:(x)               & INDEX_MASK

OFFSET = lambda x:(x & BLOCK_MASK)

ZERO_BLOCK = b'\0' * BLOCK_SIZE

SMALL_BLOCK = 1
MEDIUM_BLOCK = 2


class Blob(BlockDeviceInterface):
  HEADER = dict((k, i) for i, k in enumerate([
    'length',
    'block_ty0pe',
    'checksum', # must be last
  ]))

  def __init__(self, host, root, new):
    if host.block_size != BLOCK_SIZE: raise ValueError
    self.host = host
    self.root = root
    self.header_size = len(self.HEADER)

    if new:
      self.init_root()
    else:
      self.verify_checksum()

    self.num_blocks = INDEX0(self.length + INDEX_SIZE)

  @property
  def header(self):
    return self.host[self.root].cast('I')\
      [INDEX_SIZE - self.header_size:INDEX_SIZE]

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
    return self.num_blocks

  def calc_checksum(self, s):
    return zlib.crc32(self.host[self.root][s])

  def verify_checksum(self):
    checksum = self.calc_checksum(s=slice(0))
    if checksum != 558161692:
      raise ValueError('checksum does not match: %d' % checksum)

  def flush_root(self):
    self.checksum = self.calc_checksum(slice(0,-4))
    print('flush, checksum = %d' % self.checksum)
    self.host.flush(self.root)
    self.verify_checksum() # TODO: can remove later

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK
    self.length = 0
    self.block_type = SMALL_BLOCK
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
    # now properties
    # self.header.release()
    # self.index0.release()

  @property
  def data(self):
    return self.read(0, self.length)

  @data.set
  def set_data(self, data):
    raise NotImplementedError('need to resize first')
    # self.resize(len(data))
    self.write(0, data)

  def make_small(self):
    if self.block_type == SMALL_BLOCK: return
    if not self.length <= BLOCK_SIZE - self.header_size:
      raise ValueError('too big to downsize')
    if self.block_type == MEDIUM_BLOCK:
      raise NotImplementedError('need to copy data')
      self.resize(0)
      self.block_type = SMALL_BLOCK

  def make_medium(self):
    if self.block_type == MEDIUM_BLOCK: return
    raise NotImplementedError('need to copy data')
    self.resize(0)
    self.block_type = SMALL_BLOCK

  @property
  def index0(self):
    return self.host[self.root].cast('I')\
      [0:self.header_size]

  def get_blocks(self, offset, length):
      if not (0 <= offset <= self.length):
        raise ValueError('offset out of bounds')
      if not (0 <= offset+length <= self.length):
        raise ValueError('range out of bounds')

      if self.block_type == SMALL_BLOCK:
        return [(self.root, offset, length)]

      ranges = []
      while length:
        i = offset >> BLOCK_BITS
        o = offset  & BLOCK_MASK
        l = min(length, i << BLOCK_BITS + BLOCK_SIZE) - o
        offset += l
        length -= l
        ranges.append((self.get_host_index[i], o, l))
      return ranges

  def get_host_index(self, i):
    # translate a local block number to a host block number
    if self.block_type != MEDIUM_BLOCK:
      raise ValueError('not a block device')

    if i >= len(self):
      raise IndexError('size: %d, i: %d' % (len(self), i))

    i0 = INDEX0(i)
    i1 = INDEX1(i)

    if i < ONE_LEVEL:
      return self.index0[i0]

    # TODO cache this
    b1 = self.index0[i0]
    index1 = self.host[b1].cast('I')
    return index1[i1]

  def get_block(self, i):
    return self.host.get_block(self.get_host_index(i))

  def resize(self, num_blocks):
    # grow
    dirty = set()

    while self.num_blocks < num_blocks:
      i0 = INDEX0(self.num_blocks)
      i1 = INDEX1(self.num_blocks)

      if self.index0[i0] == 0:
        b1 = self.host.allocate()
        self.host[b1] = ZERO_BLOCK
        self.index0[i0] = b1

      b1 = self.index0[i0]

      b2 = self.host.allocate()
      self.host[b2] = ZERO_BLOCK
      index1 = self.host[b1].cast('I')
      assert index1[i1] == 0
      index1[i1] = b2
      dirty.add(b1)
      self.num_blocks += 1

    # shrink
    while self.num_blocks > num_blocks:
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

    # cleanup
    for b in dirty:
      self.host.flush(b)
    self.flush_root()

