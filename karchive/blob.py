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

# block number to indexes into blob header
# for multi level page tables
INDEX0 = lambda x:ONE_LEVEL + (((x - ONE_LEVEL) >> INDEX_BITS) & INDEX_MASK)
INDEX1 = lambda x:ONE_LEVEL + (((x - ONE_LEVEL))               & INDEX_MASK)

ZERO_BLOCK = b'\0' * BLOCK_SIZE

SMALL_BLOCK = 1
MEDIUM_BLOCK = 2


class Blob(BlockDeviceInterface):
  HEADER = dict((k, i) for i, k in enumerate([
    'length',
    'block_type',
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

  @property
  def data(self):
    return self.read(0, self.length)

  @data.setter
  def set_data(self, data):
    self.resize(len(data))
    self.write(0, data)

  @property
  def index(self):
    return self.host[self.root].cast('I')\
      [0:self.header_size]

  def get_blocks(self, offset, length):
    '''
    Returns list of (block, offset, length) ranges.
    blocks are host block ids
    '''
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

  def read(self, offset, length):
    r = []
    for b, o, l in self.get_blocks(offset, length):
      r.append(self.host[b][o:o+l])
    return b''.join(r)

  def write(self, offset, data):
    i = 0
    for b, o, l in self.get_blocks(offset, len(data)):
      self.host[b][o:o+l] = data[i:i+l]
      i += l

  def get_host_index(self, i):
    # translate a local block number to a host block number
    if self.block_type != MEDIUM_BLOCK:
      raise ValueError('not a block device')

    if i >= len(self):
      raise IndexError('size: %d, i: %d' % (len(self), i))


    if i < ONE_LEVEL:
      return self.index[i]

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
    DATA_LENGTH = BLOCK_SIZE - self.header_size
    if length <= DATA_LENGTH:
      if self.block_type == MEDIUM_BLOCK:
        # grow to medium block
        raise NotImplementedError()
        # free data + page blocks, copy data to root in small block
        self.block_type = SMALL_BLOCK
      else:
        # small block to small block
        # zero fill from requested length
        self.host[self.root][length:DATA_LENGTH] = ZERO_BLOCK[length:DATA_LENGTH]
        # TODO: zero fill when growing?
      self.length = length
      return

    # requested size requires a medium block
    if self.block_type == SMALL_BLOCK:
      data = self.data
      self.block_type = MEDIUM_BLOCK
      self.length = 0
    else:
      data = None

    num_blocks = BLOCK(self.length + BLOCK_MASK)
    dirty = set()

    # grow
    if self.length < length:
      next_block = min(num_blocks * BLOCK_SIZE, length)
      s = slice(OFFSET(self.length), OFFSET(next_block))
      self.get_block(BLOCK(self.length))[s] =  ZERO_BLOCK[s]
      self.length = next_block


    while self.num_blocks < num_blocks and self.num_blocks < ONE_LEVEL:
      b1 = self.host.allocate()
      self.host[b1] = ZERO_BLOCK
      self.index[self.num_blocks] = b1
      dirty.add(b1)

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

    if data:
      # copy data from small block expansion
      self.write(0, data)

    self.length = length

    # cleanup
    for b in dirty:
      self.host.flush(b)
    self.flush_root()

  def __repr__(self):
    return '''<Blob(length=%d, block_type=%d, checksum=%s)>''' % tuple(self.header)
