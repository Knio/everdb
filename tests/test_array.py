import os

import pytest

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_array():
  db = karchive.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  ar = db.array('I')
  r = ar.root

  with pytest.raises(IndexError):
    x = ar.pop()

  with pytest.raises(NotImplementedError):
    x = ar[0:1]

  with pytest.raises(NotImplementedError):
    ar[0:1] = [1]


  N = 2000
  for i in range(N):
    ar.append(i)
    assert ar[i] == i

  assert ar.type == (N >= 1080 and 2 or 1)

  assert len(ar) == N

  # print(list(ar.get_block(0)))

  for i in range(N):
    # print('%d: %d' % (i, ar[i]))
    assert ar[i] == i

  ar.close()
  db.close()

  #############

  db = karchive.Database(TEST_NAME, readonly=True)
  db.freelist = []
  ar = karchive.Array(db, r, 'I', new=False)

  assert len(ar) == N
  for i in range(N):
    # print('%d: %d' % (i, ar[i]))
    assert ar[i] == i

  ar.close()
  db.close()

  #############

  db = karchive.Database(TEST_NAME)
  db.freeelist = []
  ar = karchive.Array(db, r, 'I', new=False)

  assert len(ar) == N
  for i in range(N-1, -1, -1):
    assert ar[i] == i
    assert ar.pop() == i
    assert ar.length == i

  assert ar.type == 1


  ar.close()
  db.close()
  os.remove(TEST_NAME)


def test_todo():
  db = karchive.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  ar = db.array('I')
  r = ar.root

  with pytest.raises(IndexError):
    x = ar.pop()

  with pytest.raises(NotImplementedError):
    x = ar[0:1]

  with pytest.raises(NotImplementedError):
    ar[0:1] = [1]

  with pytest.raises(NotImplementedError):
    ar.extend([1])


  ar.close()
  db.close()
  os.remove(TEST_NAME)



if __name__ == '__main__':
  test_array()
