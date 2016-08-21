# pylint: disable=W0311

import array
import zlib

from .blockdevice import BlockDeviceInterface
from .header      import Header, Field
from .page        import Page
from .page        import BLOCK_SIZE, BLOCK_MASK, BLOCK_BITS
from .page        import SMALL_PAGE, REGULAR_PAGE, ZERO_BLOCK

# logical page number and offset
BLOCK  = lambda x:(x >> BLOCK_BITS)
OFFSET = lambda x:(x &  BLOCK_MASK)

class Blob(Page):
  length      = Field('Q')

  def __len__(self):
    return self.length

  @property
  def data(self):
    return self.read(0, self.length)

  @data.setter
  def set_data(self, data):
    self.resize(len(data))
    self.write(0, data)

  def init_root(self):
    self.length = 0
    super(Blob, self).init_root()

  def get_blocks(self, offset, length):
    '''
    Returns list of (block, offset, length) ranges.
    blocks are host block ids
    '''
    if not (0 <= offset <= self.length):
      raise ValueError('offset out of bounds (offset: %d, blob length: %d)' % (offset, self.length))
    if not (0 <= offset + length <= self.length):
      raise ValueError('range out of bounds')

    if self.type == SMALL_PAGE:
      return [(self.root, offset, length)]

    ranges = []
    while length:
      b = BLOCK(offset)
      o = OFFSET(offset)
      l = min(length, BLOCK_SIZE - o)
      offset += l
      length -= l
      ranges.append((self.get_host_index(b), o, l))
    return ranges

  def read(self, offset=0, length=None):
    if length is None:
      length = self.length
    r = []
    for b, o, l in self.get_blocks(offset, length):
      r.append(bytes(self.host[b][o:o+l]))
    return b''.join(r)

  def write(self, offset, data):
    i = 0
    for b, o, l in self.get_blocks(offset, len(data)):
      self.host[b][o:o+l] = data[i:i+l]
      i += l
    if self.type == SMALL_PAGE:
      # TODO don't do this
      self.sync_header()

  def resize(self, length):
    '''
    Resizes the blob to a given length, by truntating it or
    extending with zero bytes.
    '''
    # requested size fits in a small block
    # handles both grow and shrink operation
    if length < 0:
      raise ValueError('length must not be negative (%d)' % length)
    if length == self.length:
      return

    MAX_SMALL = BLOCK_SIZE - self._header_size
    if length <= MAX_SMALL:
      s = slice(length, MAX_SMALL)
      if self.type == REGULAR_PAGE:
        # copy data to root in small block
        data = self.read(0, length)
        # free data + page blocks,
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
    num_blocks = BLOCK(length + BLOCK_MASK)
    cur_blocks = self.num_blocks

    if cur_blocks == num_blocks:
      # don't need to allocate or free any blocks
      # zero fill any truncated space
      if length < self.length:
        b = self.get_block(BLOCK(length - 1))
        s = slice(OFFSET(length), OFFSET(self.length - 1) + 1)
        b[s] = ZERO_BLOCK[s]
      self.length = length
      self.sync_header()
      return

    if self.type == SMALL_PAGE:
      self.make_regular()

    # allocate/free blocks
    self.allocate(num_blocks)

    self.length = length
    self.sync_header()

  def __repr__(self):
    return '''<Blob(root=%d, type=%d, num_blocks=%d, length=%d)>''' % \
        (self.root, self.type, self.num_blocks, self.length)
