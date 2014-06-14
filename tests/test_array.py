import os

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_array():
  try:  os.remove(TEST_NAME)
  except FileNotFoundError: pass
  host = karchive.Database(TEST_NAME)
  ar = karchive.Array(host, 0, 'I', new=True)

  host.close()
