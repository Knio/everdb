'''
Array of single primitive (struct) items
'''

# pylint: disable=W0311

import struct

from .blob import Blob, Field
from .blob import SMALL_BLOB, REGULAR_BLOB
from .blob import BLOCK, OFFSET
from .blob import ZERO_BLOCK, BLOCK_MASK, BLOCK_SIZE

class Array(Blob):
  capacity = Field('Q')

  def __init__(self, host, root, format, new):
    self.format = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = BLOCK_SIZE // self.item_size
    super(Array, self).__init__(host, root, new)

  def init_root(self):
    MAX_SMALL = (BLOCK_SIZE - self._header_size) // self.item_size
    self.capacity = MAX_SMALL
    super(Array, self).init_root()

  def __len__(self):
    return self.length

  def __getitem__(self, i):
    if isinstance(i, slice):
      return self.getslice(i)

    if i < 0:
      i = self.length + i
    if not (0 <= i < self.length):
      raise IndexError('index out of range: %d (length: %d)'
        % (i, self.length))

    j = i // self.items_per_block
    k = i  % self.items_per_block

    if self.type == SMALL_BLOB:
      b = self.host[self.root]
    else:
      b = self.get_block(j)

    # TODO cache this
    return b.cast(self.format)[k]

  def __setitem__(self, i, v):
    if isinstance(i, slice):
      return self.setslice(i, v)

    if not (0 <= i < self.length):
      raise IndexError()

    j = i // self.items_per_block
    k = i  % self.items_per_block

    if self.type == SMALL_BLOB:
      b = self.host[self.root]
    else:
      b = self.get_block(j)

    # TODO cache this
    b.cast(self.format)[k] = v

  def getslice(self, i):
    raise NotImplementedError

  def setslice(self, i, v):
    raise NotImplementedError

  def extend(self, iter):
    raise NotImplementedError

  def append(self, v):
    l = self.length
    assert self.capacity >= l + 1
    self.length += 1
    self[l] = v
    # ensure 1 extra slot
    if self.capacity < l + 2:
      self.resize(l + 2)

  def pop(self):
    if not self.length:
      raise IndexError
    l = self.length
    j = l - 1
    x = self[j]
    self.length = j
    if self.capacity > l + 2:
      self.resize(l + 2)
    return x

  def resize(self, capacity):
    '''
    Resizes the array to a given size (in elements, not bytes)
    '''
    # requested size fits in a small block
    # handles both grow and shrink operation
    length = capacity * self.item_size

    MAX_SMALL = (BLOCK_SIZE - self._header_size)
    if length <= MAX_SMALL:
      if self.type == REGULAR_BLOB:
        # copy data to root in small block
        data = bytes(self.get_block(0)[0:length])
        # free data + page blocks,
        self.allocate(0)
        self.host[self.root][0:length] = data
      else:
        # already a small block
        # zero fill from requested length,
        # to make sure truncated data is not leaked
        s = slice(length, MAX_SMALL)
        self.host[self.root][s] = ZERO_BLOCK[s]
        # no zero fill when growing, since we assume the block was
        # zeroed either above or on blob creation
      self.type = SMALL_BLOB
      self.capacity = capacity
      self.flush_root()
      return

    # requested size requires a regular blob
    num_blocks = BLOCK(length + BLOCK_MASK)
    cur_blocks = self.num_blocks

    if cur_blocks == num_blocks:
      # don't need to allocate or free any blocks
      # zero fill any truncated space
      i = BLOCK(length)
      if i != cur_blocks:
        b = self.get_block(i)
        s = slice(OFFSET(length), BLOCK_SIZE)
        b[s] = ZERO_BLOCK[s]
      self.capacity = capacity
      self.flush_root()
      return

    data = None
    l = self.length
    if self.type == SMALL_BLOB:
      data = bytes(self.host[self.root][0:self.length * self.item_size])
      self.type = REGULAR_BLOB
      self.length = 0
      self.capacity = 0
      # def _pop():
      #   return data.pop()
      # self.pop = _pop

    # allocate/free blocks
    # may call append/pop!
    self.allocate(num_blocks)


    # copy data back from small block expansion
    if data:
      self.get_block(0)[0:len(data)] = data
      self.length = l
      # del self.pop

    # still need this because we may have over-allocated
    # if length was not on a page boundary
    self.capacity = capacity
    self.flush_root()
