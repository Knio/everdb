import os

import msgpack
import pytest

import everdb
import everdb.hash

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
  P = 10000357
  N = 2000
  try:
    for i in range(P, P + N):
      hs[i] = i
      assert hs[i] == i
      assert len(hs) == i - P + 1

  finally:
    debug_hash(hs)

  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME, readonly=True)
  db.freelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(P, P + N):
    # print('%d: %d' % (i, ar[i]))
    assert hs[i] == i


  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME)
  db.freeelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == N
  for i in range(P + N - 1, P - 1, -1):
    assert hs.pop(i) == i

  with pytest.raises(KeyError):
    x = hs.pop(1)

  hs.close()
  db.close()

  os.remove(TEST_NAME)


if __name__ == '__main__':
  test_hash()


def debug_bucket(b):
  print('  ' + repr(b))
  h = b.get_header()
  intervals = sorted(zip(h[0::2], h[1::2]))
  for o, l in intervals:
    if not l: continue
    d = msgpack.loads(b.read(o, l))
    print('    %4d %3d %r' % (o, l, d))

def debug_hash(h):
  print(repr(h))

  if h.num_blocks == 0:
    debug_bucket(h)
  else:
    for i in range(h.num_blocks):
      b = everdb.hash.Bucket(h.host, h.get_host_index(i), False)
      debug_bucket(b)

