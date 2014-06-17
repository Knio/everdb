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
    if i >= len(self):
      raise IndexError
    j = i // self.items_per_block
    k = i  % self.items_per_block
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
    if self.items_per_block * self.block.num_blocks < (self.block.length + 1):
      # may call pop()
      print('grow: %d' % (self.block.num_blocks + 1))
      self.block.resize(self.block.num_blocks + 1)

    i = self.block.length
    self.block.length += 1
    self[i] = v

  def pop(self):
    if not self.block.length:
      raise IndexError

    x = self[self.block.length - 1]
    self.block.length -= 1

    if (self.block.num_blocks - 2) * self.items_per_block > self.block.length:
      # may call append()
      print('shrink: %d' % (self.block.num_blocks - 1))
      self.block.resize(self.block.num_blocks - 1)

    return x
