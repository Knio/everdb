import struct

from .blob import Blob
from .blob import SMALL_BLOB, REGULAR_BLOB

class Array(Blob):
  def __init__(self, host, root, format, new):
    super(Array, self).__init__(host, root, new)
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = self.host.block_size // self.item_size

  def get_block(self, i):
    if i >= len(self):
      raise IndexError
    j = i // self.items_per_block
    k = i  % self.items_per_block
    return self.get_block(j).cast(self.format), j, k

  def __len__(self):
    return self.length

  def __getitem__(self, i):
    b, j, k = self.get_block(i)
    return b[k]

  def __setitem__(self, i, v):
    b, j, k = self.get_block(i)
    b[k] = v

  def append(self, v):
    if self.items_per_block * self.num_blocks < (self.length + 1):
      # may call pop()
      print('grow: %d' % (self.num_blocks + 1))
      self.allocate(self.num_blocks + 1)

    i = self.length
    self.length += 1
    self[i] = v

  def pop(self):
    if not self.length:
      raise IndexError

    x = self[self.length - 1]
    self.block.length -= 1

    if (self.num_blocks - 2) * self.items_per_block > self.length:
      # may call append()
      print('shrink: %d' % (self.num_blocks - 1))
      self.allocate(self.num_blocks - 1)

    return x

  def resize(self, length):
    raise NotImplementedError
