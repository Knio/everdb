import struct

from .virtualaddress import VirtualAddressSpace

class Array(object):
  def __init__(self, host, root, format, new):
    self.host = host
    self.block = VirtualAddressSpace(host, root, new)
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = self.host.block_size // self.item_size

  def close(self):
    self.block.close()

  def get_block(self, i):
    j = i // self.items_per_block
    k = i %  self.items_per_block
    return self.block[j].cast(self.format), j, k

  def __len__(self):
    return self.block.length

  def __getitem__(self, i):
    b, j, k = self.get_block(i)
    return b[k]

  def __setitem__(self, i, v):
    b, j, k = self.get_block(i)
    b[k] = v

  def append(self, v):
    i = self.block.length
    if (i + 1) > (self.items_per_block * self.block.num_blocks):
      self.block.resize(self.block.num_blocks + 1)
    self.block.length += 1
    self[i] = v

