import os

import pytest

import everdb

TEST_NAME = 'test_archive.deleteme.dat'


def test_resize():
  db = everdb.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  ar = db.array('I')

  capacity = (4096 - 18) // 4
  for i in range(capacity - 1):
    ar.append(i)
    assert ar[i] == i
    assert ar.type == 1
    assert ar.length == i + 1
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i + 1]

  # small to regular block allocation
  ar.append(4)
  assert ar[capacity - 1] == 4
  assert ar.type == 2
  assert ar.length == capacity
  assert ar.capacity == 4096 // 4
  with pytest.raises(IndexError):
    j = ar[capacity]


  capacity = 4096 // 4
  for i in range(ar.length, capacity - 1):
    ar.append(i)
    assert ar[i] == i
    assert ar.type == 2
    assert ar.length == i + 1
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i + 1]

  # 1 to 2 block allocation
  ar.append(5)
  assert ar[capacity - 1] == 5
  assert ar.type == 2
  assert ar.length == capacity
  assert ar.capacity == 2 * 4096 // 4
  with pytest.raises(IndexError):
    j = ar[capacity]

  # 2 block indexing
  capacity = 2 * 4096 // 4
  for i in range(ar.length, capacity - 1):
    ar.append(i)
    assert ar[i] == i
    assert ar.type == 2
    assert ar.length == i + 1
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i + 1]

  # going down

  for i in range(ar.length - 1, 4096 // 4 - 1, -1):
    assert ar.pop() == i
    assert ar.type == 2
    assert ar.length == i
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i]

  # item that caused 1->2 allocation
  assert ar.pop() == 5
  assert ar.length == 1023
  assert ar.capacity == 2 * 4096 // 4

  # prev item should cause 2->1 shrink
  assert ar.pop() == 1022
  assert ar.length == 1022
  assert ar.capacity == 4096 // 4

  capacity = 4096 // 4
  for i in range(ar.length - 1, (4096 - 18) // 4 - 1, -1):
    assert ar.pop() == i
    assert ar.type == 2
    assert ar.length == i
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i]

  # item that caused 0->1 allocation
  assert ar.pop() == 4
  assert ar.type == 2
  assert ar.length == 1018
  assert ar.capacity == capacity

  # prev item should cause 1->0 allocation
  assert ar.pop() == 1017
  assert ar.length == 1017
  assert ar.type == 1
  assert ar.capacity == (4096 - 18) // 4

  capacity = (4096 - 18) // 4
  for i in range(ar.length - 1, -1, -1):
    assert ar.pop() == i
    assert ar.type == 1
    assert ar.length == i
    assert ar.capacity == capacity
    with pytest.raises(IndexError):
      j = ar[i]

def test_array():
  db = everdb.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  ar = db.array('I')
  r = ar.root

  assert everdb.Array._header_size == 18

  with pytest.raises(IndexError):
    x = ar.pop()

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

  db = everdb.Database(TEST_NAME, readonly=True)
  # db.freelist = []
  ar = everdb.Array(db, r, 'I', new=False)

  assert len(ar) == N
  for i in range(N):
    # print('%d: %d' % (i, ar[i]))
    assert ar[i] == i

  ar.close()
  db.close()

  #############

  db = everdb.Database(TEST_NAME)
  # db.freeelist = []
  ar = everdb.Array(db, r, 'I', new=False)

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
  db = everdb.Database(TEST_NAME, overwrite=True)
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
