

class BlockAllocatorMixin(object):
  '''
  implements an allocate() and free(block) interface
  '''
  def __init__(self, *args):
    super(object, self).__init__(*args)
    self.free_blocks = < free list >


  def allocate(self):
    if len(self.free_blocks):
      return self.free_blocks.pop()
    else:
      b = len(self)
      self.resize(b + 1)
      return b

  def free(self, block):
    self.free_blocks.append(block)
