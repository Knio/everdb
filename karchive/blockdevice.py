import io
import os
import mmap
import struct


class BlockDevice(object):
  '''
  A device that allocates and frees blocks backed by a disk file
  '''

  @classmethod
  def create(cls, fname, block_size=4096):
    f = open(fname, 'w+b')
    f.write(b'\0' * block_size)
    f.flush()
    if os.name == 'nt':
      m = mmap.mmap(f.fileno(), block_size, access=mmap.ACCESS_WRITE)
    else:
      raise NotImplementedError
    return cls(True, f, m, block_size)

  @classmethod
  def open(cls, fname, block_size=4096):
    l = os.path.getsize(fname)
    f = open(fname, 'r+b')
    if os.name == 'nt':
      m = mmap.mmap(f.fileno(), l, access=mmap.ACCESS_WRITE)
    else:
      raise NotImplementedError
    return cls(False, f, m, block_size)

  def __init__(self, new, file, mmap, block_size):
    self.file = file
    self.mmap = mmap
    self.view = memoryview(self.mmap)
    self.block_size = block_size

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
    self.length_bytes = num_blocks * self.block_size
    self.view.release()
    self.mmap.resize(self.length_bytes)
    self.view = memoryview(self.mmap)

  def get_block(self, i):
    s = i * self.block_size
    e = s + self.block_size
    return self.view[s:e]

  def set_block(self, i, v):
    s = i * self.block_size
    e = s + self.block_size
    self.view[s:e] = v

  __getitem__ = get_block
  __setitem__ = set_block

  def size(self):
    return len(self.mmap) // self.block_size

  __len__ = size



