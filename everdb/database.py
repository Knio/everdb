import os

from .fileblockdevice   import FileBlockDevice

from .blob              import Blob
from .array             import Array
from .hash              import Hash

class Database(FileBlockDevice):
  def __init__(self, *args, **kwargs):
    super(Database, self).__init__(*args, **kwargs)
    if self.is_new:
      # allocate root for freelist
      self.freelist = []
      assert self.allocate() == 1
    self.freelist = Array(self, 1, 'I', new=self.is_new)

  def allocate(self):
    if self.freelist:
      # may call free()
      block = self.freelist.pop()
    else:
      block = len(self)
      self.resize(block + 1)

    return block

  def free(self, block):
    # may call allocate()
    self.freelist.append(block)

  # create new objects
  def blob(self):
    return Blob(self, self.allocate(), True)

  def array(self, format):
    return Array(self, self.allocate(), format, True)

  def hash(self):
    return Hash(self, self.allocate(), True)
