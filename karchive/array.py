import struct

from .blob import Blob
from .blob import SMALL_BLOB, REGULAR_BLOB

class Array(Blob):
  def __init__(self, host, root, format, new):
    super(Array, self).__init__(host, root, new)
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = self.host.block_size // self.item_size

  def get_subblock(self, i):
    if i >= self.length:
      raise IndexError
    j = i // self.items_per_block
    k = i  % self.items_per_block
    return self.get_block(j).cast(self.format), j, k

  def __len__(self):
    return self.length

  def __getitem__(self, i):
    if self.type == SMALL_BLOB:
      if i >= self.length:
        raise IndexError
      return self.host[self.root].cast(self.format)[i]
    b, j, k = self.get_subblock(i)
    return b[k]

  def __setitem__(self, i, v):
    if self.type == SMALL_BLOB:
      if i >= self.length:
        raise IndexError
      self.host[self.root].cast(self.format)[i] = v
      return
    b, j, k = self.get_subblock(i)
    b[k] = v

  def append(self, v):
    l = self.length
    j = l + 1

    # TODO: optimize this
    self.resize(j * self.item_size)
    self.length = j
    self.flush_root()

    self[l] = v

  def pop(self):
    if not self.length:
      raise IndexError

    l = self.length
    j = self.length - 1
    x = self[j]

    # TODO: optimize this
    # intentionally off by 1
    l = self.length
    self.resize((l + 1) * self.item_size)
    self.length = j
    self.flush_root()

    return x
