import os

import pytest

import everdb

TEST_NAME = 'test_archive.deleteme.dat'

def test_hash():
  assert everdb.Hash._header == [
    ('level', 'B'),
    ('split', 'I'),
    ('size', 'Q'),
    ('length', 'Q'),
    ('type', 'B'),
    ('num_blocks', 'I'),
  ]

  db = everdb.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  hs = db.hash()
  r = hs.root


  # import pdb
  # pdb.set_trace()

  N = 2000
  for i in range(N):
    hs[i] = i
    assert hs[i] == i
    assert len(hs) == i + 1

  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME, readonly=True)
  db.freelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(N):
    # print('%d: %d' % (i, ar[i]))
    assert hs[i] == i

  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME)
  db.freeelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(N-1, -1, -1):
    assert hs.pop(i) == i

  with pytest.raises(KeyError):
    x = hs.pop(1)

  hs.close()
  db.close()

  os.remove(TEST_NAME)


if __name__ == '__main__':
  test_hash()
