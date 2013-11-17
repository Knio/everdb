import os
import time

import karchive

FNAME = 'test_archive.deleteme.dat'


def test_open():
  bd = karchive.BlockDevice.create(FNAME, block_size=64)
  bd.close()
  os.remove(FNAME)

def test_bd():
  # os.remove(FNAME)
  bd = karchive.BlockDevice.create(FNAME, block_size=64)
  assert len(bd) == 1
  bd.resize(2)
  assert len(bd) == 2
  bd[0] = (b'1' * 64)
  bd[1] = (b'2' * 64)
  bd.flush()
  bd.close()
  assert os.path.getsize(FNAME) == 128  

  bd = karchive.BlockDevice.open(FNAME, block_size=64)
  assert len(bd) == 2
  assert bd[0] == b'1'*64
  assert bd[1] == b'2'*64
  bd.resize(1)
  bd.close()
  assert os.path.getsize(FNAME) == 64 

