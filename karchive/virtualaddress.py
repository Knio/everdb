
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

class VirtualAddressBlockDevice(BlockDevice):
	def __init__(self, new, f, m, block_size, num_indexes=2):
		super(VirtualAddressBlockDevice, self).__init__(new, f, m, block_size)
    # figure out how many pages we can have/need at block size
    
  def page_by_index(self, i):
    i & 0xff000000
