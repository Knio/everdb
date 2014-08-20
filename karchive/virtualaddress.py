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
  def data(self):
    if self.block_type == BLOCK_SMALL:
      return self.host[self.root][0:self.length]
    return self.read()


  @data.set
  def set_data(self, data):
    l = len(data)
    if l <= BLOCK_SIZE - self.header_size:
      self.host[self.root][0:l] = data
      self.length = l
      return

    raise NotImplementedError

  def make_small(self):
    if not self.block_type == 2:
      raise ValueError
    if not self.length <= BLOCK_SIZE - self.header_size
    data = self.data


  @property
  def index0(self):
    return self.host[self.root].cast('I')\
      [0:self.header_size]

  @property
  def header(self):
    return self.host[self.root].cast('I')\
      [INDEX_SIZE - self.header_size:INDEX_SIZE]

  def size(self):
    return self.num_blocks

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK
    self.length = 0
    self.block_type = 1
    self.flush_root()

  def calc_checksum(self):
    print(self.header.tolist())
    return zlib.crc32(self.host[self.root][:-4])

  def flush_root(self):
    self.checksum = self.calc_checksum()
    print('flush, checksum = %d' % self.checksum)
    self.host.flush(self.root)
    self.verify_checksum()

  def flush(self, block=-1):
    if block == -1:
      self.host.flush()
    else:
      self.host.flush(self.get_host_index(block))

  def close(self):
    if not self.host.readonly:
      self.flush_root()
      self.flush()
    # now properties
    # self.header.release()
    # self.index0.release()

  def verify_checksum(self):
    checksum = self.calc_checksum()
    if checksum != self.checksum:
      raise ValueError('checksum does not match: %d != %d' % (checksum, self.checksum))

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

