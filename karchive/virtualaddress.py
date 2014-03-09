
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
from .blockdevice import BlockDevice

meta = dict(k, i for i, k in enumerate([
  'length',
  'checksum',
]))

BLOCK_BITS = (12)
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

INDEX0 = lambda x:x >> 10
INDEX0 = lambda x:x >> 10

class VirtualAddressSpace(object):
	def __init__(self, device, block, new):
    raise ValueError if device.block_size != 4096
    self.device = device
    self.block = block
    self.dirty = False

    uint = self.device[self.block].cast('I')
    self.index0 = uint[   0: 992]
    self.meta   = uint[ 992:1024]

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

  def get(self, i):
    if i >= self.length // BLOCK_SIZE:
      return IndexError
    i0 = INDEX_MASK & (i >> INDEX_BITS)
    i1 = INDEX_MASK & (i >> INDEX_BITS * 2)

    b1 = self.index0[i0]
    index1 = self.get_index(b1)
    b2 = index1[i1]
    return self.device[b2]


  def read(self, offset, length):
    if offset >= self.length:
      return ''
    data = []
    while offset < self.length:


  def write(self, offset, data):
    pass