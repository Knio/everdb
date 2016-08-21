import os

import everdb

TEST_NAME = '_everdb.test.deleteme'

def test_page_type():
  assert everdb.Page._header == [
      ('type', 'B'),
      ('num_blocks', 'I'),
  ]
  assert everdb.Page._header_fmt == '!BI'
  assert everdb.Page._header_size == 9

def test_page():
  db = everdb.Database(TEST_NAME, overwrite=True)
  # db.freelist = []

  page = db.page()
  assert page.type == 1
  assert page.num_blocks == 0

  page.make_regular()
  assert page.type == 2
  assert page.num_blocks == 1

  for i in range(1, 1 + 512):
    page.allocate(i)
    assert page.num_blocks == i

  assert page.num_blocks == 512
  assert page.index[512] == 0
  assert list(page.index[:512]) == list(range(3, 3+512))

  page.allocate(512 + 1)
  assert page.index[512] == 515
  assert db[515].cast('I')[0] == 516

  for i in range(512 + 1, 512 + 1 + 1024):
    page.allocate(i)
    assert page.num_blocks == i

  assert list(db[515].cast('I')) == list(range(516, 516 + 1024))
  assert list(page.index[:512]) == list(range(3, 3+512))

  page.allocate(512 + 1024 + 1)
  assert page.index[513] == 516 + 1024
  assert db[516 + 1024].cast('I')[0] == 516 + 1024 + 1

  # go down

  page.allocate(512 + 1024)
  assert page.index[513] == 0
  assert list(page.index[:512]) == list(range(3, 3+512))

  for i in range(512 + 1024 - 1, 512 - 1, -1):
    page.allocate(i)

  assert page.index[512] == 0
  assert list(page.index[:512]) == list(range(3, 3+512))

  page.allocate(511)
  assert list(page.index[:512]) == list(range(3, 3+511)) + [0]


  # n = 100000
  # for i in range(n):
  #   page.allocate(i)

  # for i in range(n - 1, -1, -1):
  #   page.allocate(i)

  page.close()
  db.close()
  os.remove(TEST_NAME)

def test_large_page():
  db = everdb.Database(TEST_NAME, overwrite=True)
  # db.freelist = []

  page = db.page()
  page.make_regular()

  n = 100000
  for i in range(n):
    page.allocate(i)

  for i in range(n - 1, -1, -1):
    page.allocate(i)

  page.close()
  db.close()
  os.remove(TEST_NAME)
