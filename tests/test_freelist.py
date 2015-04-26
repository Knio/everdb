import os
import pdb

import everdb

TEST_NAME = 'test_archive.deleteme.dat'

def test_freelist():
  host = everdb.Database(TEST_NAME, overwrite=True)

  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  # allocates new block
  a = host.allocate()
  assert a == 2
  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  # saves freed block to freelist small blob
  host.free(a)
  assert len(host.freelist) == 1
  assert tuple(host.freelist) == (a,)

  # reuses the freed block
  b = host.allocate()
  assert b == a
  assert len(host.freelist) == 0
  assert tuple(host.freelist) == ()

  # allocate 3 pages worth (does not change the freelist)
  for i in range(3, 3 + 1024):
    b = host.allocate()
    assert b == i
  for i in range(3 + 1024, 3 + 1024 + 1024):
    b = host.allocate()
    assert b == i
  for i in range(3 + 1024 + 1024, 3 + 1024 + 1024 + 1024):
    b = host.allocate()
    assert b == i

  XX = 1018
  # fill small block of freelist
  for i in range(3, 3 + XX):
    host.free(i)
    assert host.freelist[-1] == i
  assert host.freelist.type == 1
  assert host.freelist.capacity == XX + 1
  assert host.freelist.length == XX
  assert host.freelist.num_blocks == 0

  # causes freelist to become regular blob, allocating 3 + 1018
  # pdb.set_trace()
  host.free(3 + XX)
  # freelist.append(1020)
  #   freelist.resize(1020 * 4)
  #     freelist.allocate(1)
  #       host.allocate()
  #         freelist.pop() -> 1020 + 3
  #           freelist.resize(1017 * 4)
  #             needs to stop here
  #             does not call free
  #
  assert host.freelist.type == 2
  assert host.freelist.capacity == 1024
  assert host.freelist.index[0] == XX + 3
  # print(tuple(host.freelist))

  assert tuple(host.freelist) == tuple(range(3, 3 + XX))
  assert host.freelist.num_blocks == 1


  assert host.freelist.length == XX
  assert host.freelist[-1] == XX + 3 - 1

  for i in range(3 + XX, 3 + 1024 - 1):
    host.free(i)
    assert host.freelist.length == i - 3 + 1
    assert host.freelist[-1] == i

  assert host.freelist.num_blocks == 1
  assert host.freelist.length == 1023
  assert host.freelist.capacity == 1024

  # next free causes freelist to allocate & pop
  # the given block
  # import pdb; pdb.set_trace()
  host.free(3 + 1024 - 1)

  assert host.freelist.num_blocks == 2
  assert host.freelist.capacity == 2048
  assert host.freelist.index[1] == 3 + 1024 - 1
  assert host.freelist.length == 1023
  assert host.freelist[-1] == 1023 + 3 - 1


  assert host.allocate() == 1023 + 3 - 1
  assert host.freelist.num_blocks == 1
  assert host.freelist.capacity == 1024
  assert host.freelist.length == 1023
  assert host.freelist[-1] == 1024 + 3 - 1

  # causes freelist to shrink
  assert host.allocate() == 1024 + 3 - 1
  # calls free(3 + 1024 + 1)
  assert host.freelist.num_blocks == 1
  assert host.freelist.capacity == 1024
  assert host.freelist.length == 1022
  assert host.freelist[-1] == 1022 + 3 - 1

  assert host.allocate() == 1022 + 3 - 1
  assert host.freelist.type == 2
  assert host.allocate() == 1021 + 3 - 1
  assert host.freelist.type == 2
  assert host.allocate() == 1020 + 3 - 1
  assert host.freelist.type == 2
  assert host.allocate() == 1019 + 3 - 1
  assert host.freelist.type == 2

  # causes shrink to small
  assert host.allocate() == 1018 + 3 - 1
  assert host.freelist.type == 1
  assert host.freelist.capacity == 1019

  host.close()
  os.remove(TEST_NAME)
  return
  assert False

  for i in range(5 + 1024, 5 + 1024 + 1024):
    host.free(i)
  assert host.freelist.num_blocks == 2
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  del index1


  # 2nd free causes freelist to allocate & pop
  # the last item on freelist = (5 + 1024 + 1024)
  for i in range(5 + 1024 + 1024, 5 + 1024 + 1024 + 1024):
    host.free(i)
  assert host.freelist.num_blocks == 3
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

  assert host.freelist.num_blocks == 3
  assert tuple(host.freelist) == tuple(range(5, 5 + 1024 - 1)) + (5 + 1024,)
  index1 = host[3].cast('I')
  assert index1[0] == 4
  assert index1[1] == 5 + 1024 - 1
  assert index1[2] == 5 + 1024 + 1024
  del index1

  # allocation should cause freelist to free block 5 + 1024 + 1024
  c = host.allocate()
  assert host.freelist.num_blocks == 2
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
