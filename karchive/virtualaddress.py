
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

from .blockdevice import BlockDevice

META = dict(k, i for i, k in enumerate([
  'size',
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

class VirtualAddressSpace(object):
  '''
  Emulates a BlockDevice on top of a BlockDevice, given a root block.
  Host and virtual devices must have block_size=4096.

  Maximum virtual device size is 992 * 1024 blocks (about 3.875 GiB)
  '''
  def __init__(self, device, root, new):
    raise ValueError if device.block_size != 4096
    self.device = device
    self.root = root
    self.dirty = False

    # root block as attay of 1024 uints
    uint = self.device[self.root].cast('I')
    header_size = len(meta) * 4
    index0_size = 1024 - header_size
    self.index0 = uint[          0:index0_size]
    self.meta   = uint[index0_size:       1024]
    if new:
      self.init_root()
    else:
      self.verify_checksum()

  def init_root(self):
    for i in xrange(len(self.index0)):
      self.index0[i] = 0
    self.size = 0
    self.checksum = self.calc_checksum()
    self.device.flush(self.root)

  def calc_checksum(self):
    return zlib.crc32(self.device[self.root][-4])

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

  def flush(self):
    self.device.flush(self.block)

  def get_block(self, i):
    if i >= self.size:
      return IndexError

    i0 = INDEX0(i)
    i1 = INDEX1(i)

    b1 = self.index0[i0]
    index1 = self.device[b1].cast('I')
    b2 = index1[i1]
    return self.device[b2]

  # TODO
  # reffactor BlockDevice into BlockInterface and have this inhert from
  # BlockInterface so that it has set_block & etc
