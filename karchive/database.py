import os


from .fileblockdevice   import FileBlockDevice
from .virtualaddress    import VirtualAddressSpace
from .array             import Array

class Database(FileBlockDevice):
  def __init__(self, *args, **kwargs):
    super(Database, self).__init__(*args, **kwargs)

    # TODO IMPLEMENT THIS
    self.freeblocks = []

  def allocate(self):
    try:
      return self.freeblocks.pop()
    except IndexError:
      block = len(self)
      self.resize(block + 1)
      return block

  def free(self, block):
    self.freeblocks.append(block)



