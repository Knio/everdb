import os


from .fileblockdevice   import FileBlockDevice
from .virtualaddress    import VirtualAddressSpace
from .array             import Array

class Database(FileBlockDevice):
  def __init__(self, *args, **kwargs):
    super(Database, self).__init__(*args, **kwargs)
    if self.is_new:
      self.freelist = []
      assert self.allocate() == 1
    self.freelist = Array(self, 1, 'I', new=self.is_new)
    self.blockviews = set()

  def allocate(self):
    if len(self.freelist):
      # may call free()
      block = self.freelist.pop()
    else:
      block = len(self)
      self.resize(block + 1)

    return block

  def free(self, block):
    # may call allocate()
    self.freelist.append(block)

  def commit(self):
    for bv in self.blockviews:
      bv.commit()

  def rollback(self):
    for bv in self.blockviews:
      bv.rollback()



