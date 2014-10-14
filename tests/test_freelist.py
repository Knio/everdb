import os

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def _test_freelist():
  host = karchive.Database(TEST_NAME, overwrite=True)

  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  # allocates new block
  a = host.allocate()
  assert a == 2
  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  # saves freed block to freelist
  # allocates 3 -> page table
  # allocates 4 -> data page
  host.free(a)
  assert len(host.freelist) == 1
  assert tuple(host.freelist) == (a,)
  assert host.freelist.block.index0[0] == 3
  index1 = host[3].cast('I')
  assert index1[0] == 4
  del index1

  # reuses the freed block
  b = host.allocate()
  assert b == a
  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  for i in range(5, 5 + 1024):
    b = host.allocate()
    assert b == i
  for i in range(5 + 1024, 5 + 1024 + 1024):
    b = host.allocate()
    assert b == i
  for i in range(5 + 1024 + 1024, 5 + 1024 + 1024 + 1024):
    b = host.allocate()
    assert b == i

  # fill 1 page of freelist
  for i in range(5, 5 + 1024):
    host.free(i)
  assert host.freelist.block.num_blocks == 1


  # next free causes freelist to allocate & pop
  # the last item on freelist = (5 + 1024 - 1)
  for i in range(5 + 1024, 5 + 1024 + 1024):
    host.free(i)
  assert host.freelist.block.num_blocks == 2
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  del index1


  # 2nd free causes freelist to allocate & pop
  # the last item on freelist = (5 + 1024 + 1024)
  for i in range(5 + 1024 + 1024, 5 + 1024 + 1024 + 1024):
    host.free(i)
  assert host.freelist.block.num_blocks == 3
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  assert index1[2] == 5 + 1024 + 1024
  del index1

  assert tuple(host.freelist) == \
      tuple(range(5, 5 + 1024 - 1)) \
    + tuple(range(5 + 1024, 5 + 1024 + 1024)) \
    + tuple(range(5 + 1024 + 1024 + 1, 5 + 1024 + 1024 + 1024))

  blocks = []
  # allocate until freelist has 1024 items
  while len(host.freelist) > 1024:
    blocks.append(host.allocate())

  assert host.freelist.block.num_blocks == 3
  assert tuple(host.freelist) == tuple(range(5, 5 + 1024 - 1)) + (5 + 1024,)
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  assert index1[2] == 5 + 1024 + 1024
  del index1

  # allocation should cause freelist to free block 5 + 1024 + 1024
  c = host.allocate()
  assert host.freelist.block.num_blocks == 2
  assert c == 5 + 1024
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  assert index1[2] == 0
  del index1

  # check
  d = host.allocate()
  assert d == 5 + 1024 + 1024




  host.close()
  os.remove(TEST_NAME)

if __name__ == '__main__':
  test_array()
