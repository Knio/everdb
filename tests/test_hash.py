import os

import msgpack
import pytest
import random

import everdb
import everdb.hash

TEST_NAME = '_everdb.test.deleteme'


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
  N = 1000
  S = list(set(random.randint(0, 10000000) for i in range(N)))
  try:
    for i, v in enumerate(S):
      hs[v] = i
      assert hs[v] == i
      assert len(hs) == i + 1

  finally:
    pass
    debug_hash(hs)

  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME, readonly=True)
  db.freelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == len(S)
  for i, v in enumerate(S):
    # print('%d: %d' % (i, ar[i]))
    assert hs[v] == i


  hs.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME)
  db.freeelist = []
  hs = everdb.Hash(db, r, new=False)

  assert len(hs) == len(S)
  for i, v in enumerate(S):
    assert hs.pop(v) == i
    assert len(hs) == len(S) - i - 1

  with pytest.raises(KeyError):
    x = hs.pop(1)

  hs.close()
  db.close()

  os.remove(TEST_NAME)


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

  if h.level == 0 and h.split == 0:
    debug_bucket(h)
  else:
    for i in range(h.num_blocks):
      b = everdb.hash.Bucket(h.host, h.get_host_index(i), False)
      debug_bucket(b)


if __name__ == '__main__':
  test_hash()
