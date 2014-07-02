
BLOCK_BITS = (12)
BLOCK_SIZE = (1 << BLOCK_BITS)
BLOCK_MASK = (BLOCK_SIZE - 1)

INDEX_BITS = (10)
INDEX_SIZE = (1 << INDEX_BITS)
INDEX_MASK = (INDEX_SIZE - 1)

INDEX0 = lambda x:(x >> INDEX_BITS) & INDEX_MASK
INDEX1 = lambda x:(x)               & INDEX_MASK


def f(x):
  next_block0 = (x + INDEX_SIZE) & (~INDEX_MASK)
  return next_block0


def test_f():
  assert f(0) == 1024
  assert f(1) == 1024
  assert f(1023) == 1024
  assert f(1024) == 2048
  assert f(1025) == 2048
