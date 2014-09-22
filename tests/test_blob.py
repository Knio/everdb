import os
import time

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_db():
  db = karchive.Database(TEST_NAME, overwrite=True)

  blob = db.blob()

  blob.resize(5)
  blob.write(0, b'AAAAA')

  r = blob.root

  db.close()
  assert os.path.getsize(TEST_NAME) == 12288

  #############

  db = karchive.Database(TEST_NAME)
  blob = karchive.Blob(db, r)
  assert blob.read() == b'AAAAA'
  db.close()
  os.remove(TEST_NAME)
