import struct

from .blob import Blob
from .blob import SMALL_BLOB, REGULAR_BLOB
from .blob import BLOCK, OFFSET
from .blob import ZERO_BLOCK, BLOCK_MASK, BLOCK_SIZE

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

  def append(self, v):
    l = self.length
    j = l + 1
    self.resize(j)
    self[l] = v

  def pop(self):
    if not self.length:
      raise IndexError
    l = self.length
    j = l - 1
    x = self[j]
    self.resize(j)
    return x

  def resize(self, items):
    '''
    Resizes the array to a given size (in elements, not bytes)
    '''
    # requested size fits in a small block
    # handles both grow and shrink operation
    length = items * self.item_size

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
      self.length = items
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
      self.length = items
      self.flush_root()
      return

    data = None
    if self.type == SMALL_BLOB:
      data = bytes(self.host[self.root][0:self.length * self.item_size])
      self.type = REGULAR_BLOB
      self.length = 0

    # allocate/free blocks
    # may call append/pop!
    self.allocate(num_blocks)

    # still need this because we may have over-allocated
    # if length was not on a page boundary
    self.length = items
    self.flush_root()

    # copy data back from small block expansion
    if data:
      self.get_block(0)[0:len(data)] = data
