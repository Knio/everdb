
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

BLOCK_BITS = (12)
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

INDEX0 = lambda x:(x >> INDEX_BITS) & INDEX_MASK
INDEX1 = lambda x:(x)               & INDEX_MASK

ZERO_BLOCK = b'\0' * BLOCK_SIZE

class VirtualAddressSpace(BlockDeviceInterface):
  '''
  Emulates a BlockDevice on top of a BlockDevice, given a root block.
  Host and virtual devices must have block_size=4096.

  Maximum virtual device size is (1024 - HEADER_SIZE) * 1024 blocks,
  Which will probably be just under 4GiB
  '''

  HEADER = dict((k, i) for i, k in enumerate([
    'length',
    'num_blocks',
    'checksum', # must be last
  ]))

  def __init__(self, host, root, new):
    if host.block_size != BLOCK_SIZE: raise ValueError
    self.host = host
    self.root = root
    self.dirty = False

    # root block as array of INDEX_SIZE uints
    uint = self.host[self.root].cast('I')
    header_size = len(self.HEADER) * 4
    index0_size = INDEX_SIZE - header_size
    self.index0 = uint[          0:index0_size]
    self.header = uint[index0_size: INDEX_SIZE]
    if new:
      self.init_root()
    else:
      self.verify_checksum()

  def size(self):
    return self.num_blocks

  def init_root(self):
    self.host[self.root] = ZERO_BLOCK
    self.length = 0
    self.num_blocks = 0
    self.flush_root()

  def calc_checksum(self):
    return zlib.crc32(self.host[self.root][:-4])

  def flush_root(self):
    self.checksum = self.calc_checksum()
    self.host.flush(self.root)

  def verify_checksum(self):
    if not self.calc_checksum() == self.checksum:
      raise ValueError('checksum does not match')

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
    self.dirty = True

  def get_host_index(self, i):
    if i >= len(self):
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

  def close(self):
    self.flush()
    self.header.release()
    self.index0.release()

  def resize(self, num_blocks):
    # grow
    while self.num_blocks < num_blocks:
      # only resize up till next boundry (ie. 1024)
      next_block0 = (self.num_blocks + INDEX_SIZE) & ~INDEX_MASK
      k = min(next_block0, num_blocks)
      i0 = INDEX0(k - 1)
      i1 = INDEX1(k - 1)

      if self.index0[i0] == 0:
        b1 = self.host.allocate()
        self.host[b1] = ZERO_BLOCK
        self.index0[i0] = b1

      else:
        b1 = self.index0[i0]

      index1 = self.host[b1].cast('I')

      while i1 < next_block0:
        i1 += 1
        index1[i1] = self.host.allocate()
        self.num_blocks += 1

      self.host.flush(b1)
      self.num_blocks = k



      # ###### REFERENCE
      if self.index_blocks[i0] == 0:
        index = self.archive.allocate_block()
        self.index_blocks[i0] = index
        self.index.append(array.array('I', [0] * INDEX_SIZE))
        self.dirty_index0 = True

      if self.index[i0][i1] == 0:
        block = self.archive.allocate_block()
        self.index[i0][i1] = block
        self.dirty_index1.add(i0)


      self.length = k

      # #### OLD

    while self.num_blocks < num_blocks:
      print('%d < %d' % (self.num_blocks, num_blocks))
      # current & required index1 block
      # required index1 block

      next_block = (self.num_blocks + BLOCK_SIZE) & OFFSET_MASK
      k = min(next_block, num_blocks)


      i0 = INDEX0(self.num_blocks - 1)
      i1 = INDEX1(self.num_blocks - 1)

      if self.index0[i0] == 0:
        b1 = self.host.allocate()
        self.host[b1] = ZERO_BLOCK
        self.index0[i0] = b1





      i0 = INDEX0(self.num_blocks - 1)
      j0 = INDEX0(num_blocks - 1)

      i1 = INDEX1(self.num_blocks - 1)
      j1 = INDEX1(num_blocks - 1)
      print('%d %d' % (i0, j0))

      if i0 < j0:
        # do we need another index0 block?
        b1 = self.host.allocate()
        i0 += 1
        self.index0[i0] = b1
        self.host[b1][:] = '\0' * BLOCK_SIZE



      i1 = INDEX1(self.num_blocks - 1)
      j1 = INDEX1(min(num_blocks, (i0 + 1) << INDEX_BITS) - 1)
      print('%d %d' % (i1, j1))

      b1 = self.index0[i0]
      index1 = self.host[b1].cast('I')
      while i1 < j1:
        i1 += 1
        index1[i1] = self.host.allocate()
        self.num_blocks += 1
      self.host.flush(b1)

    # shrink
    while self.num_blocks > num_blocks:
      i0 = INDEX0(self.num_blocks - 1)
      j0 = INDEX0(num_blocks - 1)

      i1 = INDEX1(self.num_blocks - 1)
      j1 = INDEX1(min(num_blocks, i0 << INDEX_BITS))
      # 1200 -> 1024 (0)
      # 1024 -> 1023
      # 1023 -> 1022

      b1 = self.index0[i0]
      index1 = self.host[b1].cast('I')
      while i1 > j1:
        self.host.free(index1[i1])
        i1 -= 1
        self.num_blocks -= 1

      if i0 > j0:
        self.index0[i0] = 0
        self.host.free(b1)
        i0 -= 1

    self.flush_root()

