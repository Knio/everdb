import everdb

TEST_NAME = '_everdb.test.deleteme'

def test_multi():
  db = everdb.Database(TEST_NAME, overwrite=True)
  db.freelist = []
  ar = db.array('!IIQBd')

  ar.append((1, 2, 3, 4, 5.0))
  assert ar[0] == (1, 2, 3, 4, 5.0)

  ar.close()
  db.close()
  os.remove(TEST_NAME)
