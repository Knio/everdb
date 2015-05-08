'''
Array of single primitive (struct) items
'''

# pylint: disable=W0311

import struct
import weakref

from .page import Page, Field
from .page import SMALL_PAGE, REGULAR_PAGE
from .page import ZERO_BLOCK, BLOCK_MASK, BLOCK_SIZE

class Array(Page):
  format    = Field('c')
  length    = Field('Q')

  def __init__(self, host, root, format, new):
    self.format = format.encode('ascii')
    self.format_ascii = format
    self.item_size = struct.calcsize(format)
    self.items_per_block = BLOCK_SIZE // self.item_size
    self.block_cache = weakref.WeakValueDictionary()
    super(Array, self).__init__(host, root, new)

  def init_root(self):
    MAX_SMALL = (BLOCK_SIZE - self._header_size) // self.item_size
    self.length = 0
    super(Array, self).init_root()

  @property
  def capacity(self):
    if self.type == SMALL_PAGE:
      MAX_SMALL = (BLOCK_SIZE - self._header_size)
      return MAX_SMALL // self.item_size
    return self.num_blocks * self.items_per_block

  def __len__(self):
    return self.length

  def get_array_block(self, j):
    try:
      return self.block_cache[j]
    except KeyError:
      if j == -1:
        b = self.host[self.root]
      else:
        b = self.get_block(j)
      b = b.cast(self.format_ascii)
      self.block_cache[j] = b
      self.host.cache(b)
      return b

  def __getitem__(self, i):
    if isinstance(i, slice):
      return self.getslice(i)

    if i < 0:
      i = self.length + i

    if not (0 <= i < self.length):
      raise IndexError('index out of range: %d (length: %d)'
        % (i, self.length))

    if self.type == SMALL_PAGE:
      j = -1
      k = i

    else:
      j = i // self.items_per_block
      k = i  % self.items_per_block

    b = self.get_array_block(j)
    return b[k]

  def __setitem__(self, i, v):
    if isinstance(i, slice):
      return self.setslice(i, v)

    if i < 0:
      i = self.length + i

    if not (0 <= i < self.length):
      raise IndexError()

    if self.type == SMALL_PAGE:
      j = -1
      k = i

    else:
      j = i // self.items_per_block
      k = i  % self.items_per_block

    b = self.get_array_block(j)
    b[k] = v
    return v

  def getslice(self, i):
    raise NotImplementedError

  def setslice(self, i, v):
    raise NotImplementedError

  def extend(self, iter):
    raise NotImplementedError

  def append(self, v):
    l = self.length
    n = self.num_blocks

    if n == 0:
      p = (BLOCK_SIZE - self._header_size) // self.item_size
      j = -1
      k = l

    else:
      p = self.items_per_block
      j = l // p
      k = l  % p

    self.length += 1

    # TODO fix allocation if user manually filled a block to capacity
    assert j < n

    try:
      b = self.block_cache[j]
    except KeyError:
      b = self.get_array_block(j)
    b[k] = v
    del b

    # an allocate here may cause a pop(),
    # and that pop must not cause free.
    if k + 1 >= p:
      if n == 0:
        self.make_regular()
      elif j + 1 == n:
        self.allocate(n + 1)

  def pop(self):
    l = self.length - 1
    n = self.num_blocks

    if l == -1:
      raise IndexError

    if n == 0:
      p = (BLOCK_SIZE - self._header_size) // self.item_size
      j = -1
      k = l

    elif n == 1:
      p = (BLOCK_SIZE - self._header_size) // self.item_size
      j = 0
      k = l

    else:
      p = self.items_per_block
      j = l // p
      k = l  % p

    try:
      b = self.block_cache[j]
    except KeyError:
      b = self.get_array_block(j)

    x = b[k]
    b[k] = 0
    del b

    self.length = l

    if k < p - 1:
      if n == 1:
        self.make_small()
      elif j + 2 == n:
        self.allocate(n - 1)

    return x

  def resize(self, length):
    '''
    Resizes the array to a given size (in elements, not bytes)
    '''
    # requested size fits in a small block
    # handles both grow and shrink operation
    MAX_SMALL = (BLOCK_SIZE - self._header_size) // self.item_size
    if length <= MAX_SMALL:
      s = slice(length, MAX_SMALL)
      if self.type == REGULAR_PAGE:
        # copy data to root in small block
        data = bytes(self.get_block(0)[0:length])
        # free data + page blocks,
        self.last_block = None
        self.allocate(0)
        self.host[self.root][0:length] = data
        self.type = SMALL_PAGE
      # already a small block
      # zero fill from requested length,
      # to make sure truncated data is not leaked
      self.host[self.root][s] = ZERO_BLOCK[s]
      # no zero fill when growing, since we assume the block was
      # zeroed either above or on blob creation
      self.length = length
      self.sync_header()
      return

    # requested size requires a regular blob
    num_blocks = (length + self.items_per_block - 1) // self.items_per_block
    cur_blocks = self.num_blocks

    if cur_blocks == num_blocks:
      # don't need to allocate or free any blocks
      # zero fill any truncated space
      i = (length - 1) // self.items_per_block
      if i != cur_blocks:
        b = self.get_block(i)
        # TODO use length:self.length, not whole block
        s = slice(length % self.items_per_block, BLOCK_SIZE)
        b[s] = ZERO_BLOCK[s]
      self.length = length
      self.sync_header()
      return

    self.last_block = None
    if self.type == SMALL_PAGE:
      self.make_regular()

    # allocate/free blocks
    # may call append/pop!
    self.allocate(num_blocks)

    self.length = length
    self.sync_header()

  def __repr__(self):
    return '''<Array(root=%d, type=%d, format=%s, num_blocks=%d, length=%d, capacity=%d)>''' % \
        (self.root, self.type, self.format, self.num_blocks, self.length, self.capacity)
