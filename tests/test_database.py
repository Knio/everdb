import os
import time

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_db():
  try:  os.remove(TEST_NAME)
  except FileNotFoundError: pass

  db = karchive.Database(TEST_NAME)
  block = db.allocate()
  db.file[block] = b'A' * 4096
  db.close()
  assert os.path.getsize(TEST_NAME) == 8192

  db = karchive.Database(TEST_NAME)
  assert db.file[block] == b'A' * 4096
  db.close()
  os.remove(TEST_NAME)

