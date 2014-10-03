import os
import time
import random

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_small_blob():
  db = karchive.Database(TEST_NAME, overwrite=True)
  blob = db.blob()

  blob.resize(5)
  assert len(blob) == 5
  blob.write(0, b'AAAAA')

  blob.resize(10)
  assert len(blob) == 10
  blob.write(5, b'BBBBB')

  blob.resize(6)
  assert len(blob) == 6
  blob.write(2, b'C')

  r = blob.root

  db.close()
  assert os.path.getsize(TEST_NAME) == 12288

  #############

  db = karchive.Database(TEST_NAME)
  blob = karchive.Blob(db, r)

  assert len(blob) == 6
  assert blob.read() == b'AACAAB'

  db.close()
  os.remove(TEST_NAME)


def blob_tester(f):
  def wrapper():
    db = karchive.Database(TEST_NAME, overwrite=True)
    db.freelist = []
    blob = db.blob()
    r = blob.root

    # run the test
    # returns the expected conterts of the blob
    data = f(blob)

    db.close()
    db = karchive.Database(TEST_NAME)
    db.freelist = []
    blob = karchive.Blob(db, r)
    assert len(blob) == len(data)
    assert blob.read() == data
  return wrapper


@blob_tester
def test_small_small(blob):
  blob.resize(5)
  blob.write(0, b'AAAAA')
  assert blob.read() == b'AAAAA'

  blob.resize(10)
  blob.write(5, b'BBBBB')
  assert blob.read() == b'AAAAABBBBB'

  blob.resize(6)
  blob.write(2, b'C')
  assert blob.read() == b'AACAAB'

  return b'AACAAB'


@blob_tester
def test_regular_1(blob):
  data = b'Hello World! ' * (1024 * 1024)
  blob.resize(len(data))
  blob.write(0, data)
  assert blob.read() == data
  return data

@blob_tester
def test_regular_2(blob):
  data = b'Hello World! ' * (1024 * 1024)
  blob.resize(len(data))
  blob.write(0, data)
  blob.resize(8000)
  assert blob.read() == data[:8000]
  return data[:8000]

@blob_tester
def test_regular_3(blob):
  data = b'Hello World! ' * (1024)
  blob.resize(len(data))
  blob.write(0, data)
  blob.resize(12000)
  assert blob.read() == data[:12000]
  blob.resize(11000)
  assert blob.read() == data[:11000]
  return data[:11000]

@blob_tester
def test_regular_small(blob):
  data = b'Hello World! ' * (1024)
  blob.resize(len(data))
  blob.write(0, data)
  blob.resize(4000)
  assert blob.read() == data[:4000]
  assert blob.type == 1
  return data[:4000]


if __name__ == '__main__':
  import cgitb
  cgitb.enable(format='text')

  test_small_to_regular()
