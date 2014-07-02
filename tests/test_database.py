import os
import time

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_db():
  db = karchive.Database(TEST_NAME, overwrite=True)
  block = db.allocate()
  db[block] = b'A' * 4096
  db.close()
  assert os.path.getsize(TEST_NAME) == 12288

  db = karchive.Database(TEST_NAME)
  assert db[block] == b'A' * 4096
  db.close()
  os.remove(TEST_NAME)

