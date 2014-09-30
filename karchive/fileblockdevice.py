# pylint: disable=missing-docstring, W0311, invalid-name
import os
import mmap
import sys
if sys.version < '3.3.0':
  view = lambda x: x
else:
  view = memoryview

from .blockdevice import BlockDeviceInterface

BLOCK_SIZE = (4096)

class FileBlockDevice(BlockDeviceInterface):
  '''
  A device that allocates and frees blocks backed by a disk file
  '''

  def __init__(self, fname, readonly=False, overwrite=False, block_size=4096):
    self.readonly = readonly
    if overwrite or not os.path.isfile(fname):
      if readonly: raise ValueError
      l = block_size
      f = open(fname, 'w+b')
      f.write(b'\0' * block_size)
      f.flush()
      self.is_new = True
    else:
      l = os.path.getsize(fname)
      f = open(fname, readonly and 'rb' or 'r+b')
      self.is_new = False

    self.block_size = block_size
    self.file = f
    self.mmap = mmap.mmap(f.fileno(), l,
        access=readonly and mmap.ACCESS_READ or mmap.ACCESS_WRITE)
    self.view = memoryview(self.mmap)

  def flush(self, block=-1):
      if block == -1:
        r = self.mmap.flush()
      else:
        r = self.mmap.flush(self.block_size * block, self.block_size)
      assert r != 0

  def close(self):
    self.view.release()
    self.mmap.close()
    self.file.close()

  def resize(self, num_blocks):
    '''
    Resize the file to be num_blocks in length.
    Will truncate or add new blocks as needed.
    '''
    length_bytes = num_blocks * self.block_size
    self.view.release()
    self.mmap.resize(length_bytes)
    self.view = memoryview(self.mmap)

  def get_block(self, i):
    '''
    Returns a memoryview of the ith block in the file
    Note: view needs to be released by the caller or release()/close() will fail.
    '''
    s = i * self.block_size
    e = s + self.block_size
    return self.view[s:e]

  @property
  def num_blocks(self):
    return self.size()

  def size(self):
    return len(self.mmap) // self.block_size
