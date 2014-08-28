# pylint: disable=bad-indentation, bad-whitespace, missing-docstring

# import structpack as sp

# class BlockHeader(sp.msg):
#   MAGIC = 0x115a1110

#   STATE_CLOSED = 1
#   STATE_OPEN_CLEAN = 2
#   STATE_OPEN_DIRTY = 3

#   magic       = sp.int
#   block_size  = sp.int
#   file_size   = sp.int
#   state       = sp.int
#   free_list   = sp.int
#   checksum    = sp.int

#   def verify(self):
#     def check(x):
#       if not x:
#         raise ValueError('verification error')
import zlib

from .blockdevice import BlockDeviceInterface

BLOCK_BITS = (12) # 4096 bytes
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

INDEX0 = lambda x:(x >> INDEX_BITS) & INDEX_MASK
INDEX1 = lambda x:(x)               & INDEX_MASK

ZERO_BLOCK = b'\0' * BLOCK_SIZE

SMALL_BLOCK = 1
MEDIUM_BLOCK = 2

class Blob(BlockDeviceInterface):
  HEADER = dict((k, i) for i, k in enumerate([
    'length',
    'block_type',
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

    self.num_blocks = INDEX1(self.length + INDEX_SIZE)

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
    self.verify_checksum() # can remove later

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
    self.write(0, data)

  def make_small(self):
    if self.block_type == SMALL_BLOCK: return
    if not self.length <= BLOCK_SIZE - self.header_size:
      raise ValueError('too big to downsize')
    if self.block_type == MEDIUM_BLOCK:
      self.resize(0)
      self.block_type = SMALL_BLOCK

  def make_medium(self):
    if self.block_type == : return
    if self.block_type == MEDIUM_BLOCK:
      self.resize(0)
      self.block_type = SMALL_BLOCK

  @property
  def index0(self):
    return self.host[self.root].cast('I')\
      [0:self.header_size]

  def get_blocks(self, offset, length):



  def read(self, offset, length):
    if not (0 <= offset <= self.length):
      raise ValueError('offset out of bounds')
    if not (0 <= offset+length <= self.length):
      raise ValueError('range out of bounds')

    if self.block_type == SMALL_BLOCK:
      return self.host[self.root][offset:offset+length]

    b = []
    raise NotImplementedError

  def write(self, offset, data):
    length = len(data)

    if self.block_type == SMALL_BLOCK and \
        offset+length <= BLOCK_SIZE - self.header_size:
      self.host[self.root][offset:offset+length] = data
      self.length = l
      return

    raise NotImplementedError

  def get_host_index(self, i):
    if i >= len(self):
      raise IndexError('size: %d, i: %d' % (len(self), i))

    i0 = INDEX0(i)
    i1 = INDEX1(i)

    b1 = self.index0[i0]
    # TODO cache this?
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

