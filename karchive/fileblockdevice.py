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
    if overwrite or not os.path.isfile(fname):
      if readonly: raise ValueError
      l = block_size
      f = open(fname, 'w+b')
      f.write(b'\0' * block_size)
      f.flush()
    else:
      l = os.path.getsize(fname)
      f = open(fname, readonly and 'rb' or 'r+b')

    self.block_size = block_size
    self.file = f
    if os.name == 'nt':
      self.mmap = mmap.mmap(f.fileno(), l, access=readonly and mmap.ACCESS_READ or mmap.ACCESS_WRITE)
    else:
      raise NotImplementedError
    self.view = memoryview(self.mmap)

  def flush(self, block=-1):
      if block == -1:
        self.mmap.flush()
      else:
        self.mmap.flush(self.block_size * block, self.block_size)

  def close(self):
    self.view.release()
    self.mmap.close()
    self.file.close()

  def resize(self, num_blocks):
    length_bytes = num_blocks * self.block_size
    self.view.release()
    self.mmap.resize(length_bytes)
    self.view = memoryview(self.mmap)

  def get_block(self, i):
    s = i * self.block_size
    e = s + self.block_size
    return self.view[s:e]

  @property
  def num_blocks(self):
    return self.size()

  def size(self):
    return len(self.mmap) // self.block_size
