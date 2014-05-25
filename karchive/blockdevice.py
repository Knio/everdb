# pylint: disable=missing-docstring, W0311, invalid-name

class BlockDeviceInterface(object):
  '''
  An abstract interface for a block device
  '''

  def flush(self, block=-1):
    raise NotImplementedError

  def close(self):
    raise NotImplementedError

  def resize(self, num_blocks):
    raise NotImplementedError

  def get_block(self, i):
    raise NotImplementedError

  def set_block(self, i, v):
    self.get_block(i)[:] = v

  def size(self):
    raise NotImplementedError

  def __getitem__(self, i):
    return self.get_block(i)

  def __setitem__(self, i, v):
    return self.set_block(i, v)

  def __len__(self):
    return self.size()
