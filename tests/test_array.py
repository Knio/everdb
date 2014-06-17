import os

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_array():
  host = karchive.Database(TEST_NAME, overwrite=True)
  ar = karchive.Array(host, 0, 'I', new=True)

  N = 10000
  for i in range(N):
    ar.append(i)

  ar.close()
  host.close()

  host = karchive.Database(TEST_NAME, readonly=True)
  ar = karchive.Array(host, 0, 'I', new=False)

  assert len(ar) == N
  for i in range(N):
    assert ar[i] == i

  ar.close()
  host.close()

  host = karchive.Database(TEST_NAME)
  ar = karchive.Array(host, 0, 'I', new=False)

  assert len(ar) == N
  for i in range(N-1, -1, -1):
    assert ar.pop() == i

  assert tuple(host.freelist) == 0

  ar.close()
  host.close()



if __name__ == '__main__':
  test_array()
