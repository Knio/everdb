import everdb

TEST_NAME = 'test_archive.deleteme.dat'

def test_page_type():
  assert everdb.Page._header == [
      ('type', 'B'),
      ('num_blocks', 'I'),
  ]
  assert everdb.Page._header_fmt == '!BI'
  assert everdb.Page._header_size == 9

def test_page():
  db = everdb.Database(TEST_NAME, overwrite=True)
  db.freelist = []

  page = db.page()
  assert page.type == 1
  assert page.num_blocks == 0

