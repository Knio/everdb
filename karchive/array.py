import struct

from .virtualaddress import VirtualAddressSpace

class Array(object):
  def __init__(self, host, root, format, new):
    self.host = host
    self.block = VirtualAddressSpace(host, root, new)
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = self.item_size / self.host.block_size

  def get_block(self, i):
    j = i / self.items_per_block
    k = i % self.items_per_block
    return self.block[j].cast(self.format), j, k

  def __getitem__(self, i):
    b, j, k = self.get_block(i)
    return b[k]

  def __setitem__(self, i, v):
    b, j, k = self.get_block(i)
    b[k] = v

  def append(self, v):
    i = self.length
    if (self.length + 1) > (self.items_per_block * self.block.num_blocks):
      self.block.resize(self.block.num_blocks + 1)
    self.length += 1
    self[i] = v

