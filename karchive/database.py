import os


from .fileblockdevice   import FileBlockDevice
from .virtualaddress    import VirtualAddressSpace
from .array             import Array

class Database(object):
  def __init__(self, filename, readonly=False):
    if os.path.isfile(filename):
      self.file = FileBlockDevice.open(filename, block_size=4096)

    else:
      if readonly: raise IOError('File %r does not exist' % filename)
      self.file = FileBlockDevice.create(filename, block_size=4096)

    # TODO IMPLEMENT THIS
    self.freeblocks = []

    self.close = self.file.close
    self.flush = self.file.flush

  def allocate(self):
    try:
      return self.freeblocks.pop()
    except IndexError:
      block = len(self.file)
      self.file.resize(block + 1)
      return block

  def free(self, block):
    self.freeblocks.append(block)



