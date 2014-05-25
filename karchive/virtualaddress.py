
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

META = dict(k, i for i, k in enumerate([
  'num_blocks',
  'checksum', # should be last
]))

BLOCK_BITS = (12)
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

INDEX0 = lambda x:(x >> INDEX_BITS) & INDEX_MASK
INDEX1 = lambda x:(x)               & INDEX_MASK

class VirtualAddressSpace(BlockDeviceInterface):
  '''
  Emulates a BlockDevice on top of a BlockDevice, given a root block.
  Host and virtual devices must have block_size=4096.

  Maximum virtual device size is 992 * 1024 blocks (about 3.875 GiB)
  '''
  def __init__(self, host, root, new):
    raise ValueError if host.block_size != BLOCK_SIZE
    self.host = host
    self.root = root
    self.dirty = False

    # root block as attay of INDEX_SIZE uints
    uint = self.host[self.root].cast('I')
    header_size = len(meta) * 4
    index0_size = INDEX_SIZE - header_size
    self.index0 = uint[          0:index0_size]
    self.meta   = uint[index0_size: INDEX_SIZE]
    if new:
      self.init_root()
    else:
      self.verify_checksum()

  def init_root(self):
    self.index0[:] = [0] * len(self.index0)
    self.num_blocks = 0
    self.flush_root()

  def calc_checksum(self):
    return zlib.crc32(self.host[self.root][-4])

  def flush_root(self):
    self.checksum = self.calc_checksum()
    self.host.flush(self.root)

  def verify_checksum(self):
    if not self.calc_checksum() == self.checksum:
      raise ValueError('checksum does not match')

  def __getattr__(self, attr):
    if attr not in META:
      raise AttributeError
    i = META[attr]
    return self.meta[i]

  def __setattr__(self, attr, value):
    if attr not in META:
      raise AttributeError
    i = META[attr]
    self.meta[i] = value
    self.dirty = True

  def get_host_index(self, i):
    if i >= self.num_blocks:
      return IndexError

    i0 = INDEX0(i)
    i1 = INDEX1(i)

    b1 = self.index0[i0]
    # TODO cache this?
    index1 = self.host[b1].cast('I')
    return index1[i1]

  def get_block(self, i):
    return self.host.get_block(self.get_host_index(i))

  def flush(self, block=-1):
    if block == -1:
      self.host.flush()
    else:
      self.host.flush(self.get_host_index(block))

  def resize(self, num_blocks):
    while self.num_blocks < num_blocks:
      # grow larger
      i0 = INDEX0(self.num_blocks)
      j0 = INDEX0(num_blocks)

      if i0 < j0:
        b1 = self.host.allocate()
        self.index0[i0] = b1
        index1 = self.host[b1].cast('I')
        index1[:] = [0] * INDEX_SIZE
        i0 += 1

      i1 = INDEX1(self.num_blocks)
      j1 = INDEX1(min(num_blocks, i0 << INDEX_BITS))

      b1 = self.index0[i0]
      index1 = self.host[b1].cast('I')
      while i1 < j1:
        index1[i1] = self.host.allocate()
        i1 += 1
      self.host.flush(b1)

      self.num_blocks = i0 << INDEX_BITS + i1

    # shrink
    while self.num_blocks > num_blocks:
      raise NotImplemented
      # TODO

    self.flush_root()

