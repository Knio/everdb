import struct

from .blob import Blob
from .blob import SMALL_BLOB, REGULAR_BLOB

MAX_SMALL = (1<<12) - len(Blob.HEADER) * 4

class Array(Blob):
  def __init__(self, host, root, format, new):
    super(Array, self).__init__(host, root, new)
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = self.host.block_size // self.item_size

  def __len__(self):
    return self.length

  def __getitem__(self, i):
    if not (0 <= i < self.length):
      raise IndexError()

    j = i // self.items_per_block
    k = i  % self.items_per_block

    if self.type == SMALL_BLOB:
      b = self.host[self.root]
    else:
      b = self.host[self.get_block(j)]

    # TODO cache this
    return b.cast(self.format)[k]


  def __setitem__(self, i, v):
    if not (0 <= i < self.length):
      raise IndexError()

    j = i // self.items_per_block
    k = i  % self.items_per_block

    if self.type == SMALL_BLOB:
      b = self.host[self.root]
    else:
      b = self.host[self.get_block(j)]

    # TODO cache this
    b.cast(self.format)[k] = v

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
