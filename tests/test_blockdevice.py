import os
import time

import karchive

TEST_NAME = 'test_archive.deleteme.dat'


def test_bd():
  bd = karchive.FileBlockDevice(TEST_NAME, block_size=64, overwrite=True)
  assert len(bd) == 1
  bd.resize(2)
  assert len(bd) == 2
  bd[0] = (b'1' * 64)
  bd[1] = (b'2' * 64)
  bd.flush()
  bd.close()
  assert os.path.getsize(TEST_NAME) == 128

  bd = karchive.FileBlockDevice(TEST_NAME, block_size=64, readonly=False)
  assert len(bd) == 2
  assert bd[0] == b'1'*64
  assert bd[1] == b'2'*64
  bd.resize(1)
  bd.close()
  assert os.path.getsize(TEST_NAME) == 64
  os.remove(TEST_NAME)

