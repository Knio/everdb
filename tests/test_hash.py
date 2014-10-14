import os

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_hash():
  db = karchive.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  hs = db.hash()
  r = hs.root

  N = 2000
  for i in range(N):
    hs[i] = i
    assert hs[i] == i
    assert len(hs) == i + 1

  hs.close()
  db.close()

  #############

  db = karchive.Database(TEST_NAME, readonly=True)
  db.freelist = []
  hs = karchive.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(N):
    # print('%d: %d' % (i, ar[i]))
    assert hs[i] == i

  hs.close()
  db.close()

  #############

  db = karchive.Database(TEST_NAME)
  db.freeelist = []
  hs = karchive.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(N-1, -1, -1):
    assert hs.pop(i) == i

  hs.close()
  db.close()



if __name__ == '__main__':
  test_hash()
