import os
import time
import random

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_small_blob():
  db = karchive.Database(TEST_NAME, overwrite=True)
  blob = db.blob()

  blob.resize(5)
  blob.write(0, b'AAAAA')
  blob.resize(10)
  blob.write(5, b'BBBBB')
  blob.resize(6)
  blob.write(2, b'C')

  r = blob.root

  db.close()
  assert os.path.getsize(TEST_NAME) == 12288

  #############

  db = karchive.Database(TEST_NAME)
  blob = karchive.Blob(db, r)

  assert blob.read() == b'AACAAB'

  db.close()
  os.remove(TEST_NAME)


def test_small_to_regular():
  db = karchive.Database(TEST_NAME, overwrite=True)
  data = b'Hello World! ' * (1024 * 1024)

  blob = db.blob()

  blob.resize(5)
  blob.write(0, b'AAAAA')

  blob.resize(len(data))
  blob.write(0, data)

  # resize to a smaller medium blob
  blob.resize(8000)

  r = blob.root
  db.close()
  assert os.path.getsize(TEST_NAME) == 13656064

  #############

  db = karchive.Database(TEST_NAME)
  blob = karchive.Blob(db, r)

  assert blob.read() == data[:8000]

  db.close()
  os.remove(TEST_NAME)


if __name__ == '__main__':
    import cgitb
    cgitb.enable(format='text')

    test_small_to_regular()
