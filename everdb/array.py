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
    self.last_block = None
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

    if self.type == SMALL_PAGE:
      b = self.host[self.root]
    else:
      b = self.get_block(j)

    # TODO SLOW cache this
    return b.cast(self.format_ascii)[k]

  def __setitem__(self, i, v):
    if isinstance(i, slice):
      return self.setslice(i, v)

    if not (0 <= i < self.length):
      raise IndexError()

    j = i // self.items_per_block
    k = i  % self.items_per_block

    if self.type == SMALL_PAGE:
      b = self.host[self.root]
    else:
      b = self.get_block(j)
      if j == self.num_blocks - 1:
        c = b.cast(self.format_ascii)
        self.last_block = weakref.ref(c)
        self.host.cache(c)

    # TODO SLOW cache this
    b.cast(self.format_ascii)[k] = v

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
      self.last_block()[k] = v
    except:
      self[l] = v

    # ensure 1 extra slot
    if n == 0:
      c = (BLOCK_SIZE - self._header_size) // self.item_size
      if l > c - 2:
        self.last_block = None
        self.make_regular()

    elif k > p - 2:
      self.last_block = None
      self.allocate(n + 1)

  def pop(self):
    l = self.length - 1
    n = self.num_blocks

    if l == -1:
      raise IndexError

    if n == 0:
      j = -1
      k = l

    else:
      p = self.items_per_block
      j = l // p
      k = l  % p

    try:
      # raise
      # b = self.last_block()
      x = b[k]
      b[k] = 0
    except:
      x = self[l]
      self[l] = 0

    self.length = l

    if n == 1:
      if (BLOCK_SIZE - self._header_size) // self.item_size > l + 1:
        self.last_block = None
        self.make_small()

    elif n > 1:
      if (n - 1) * p > l + 1:
        self.last_block = None
        self.allocate(self.num_blocks - 1)

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
      self.flush_root()
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
      self.flush_root()
      return

    self.last_block = None
    if self.type == SMALL_PAGE:
      self.make_regular()

    # allocate/free blocks
    # may call append/pop!
    self.allocate(num_blocks)

    self.length = length
    self.flush_root()

  def __repr__(self):
    return '''<Array(root=%d, type=%d, format=%s, num_blocks=%d, length=%d)>''' % \
        (self.root, self.type, self.format, self.num_blocks, self.length)
