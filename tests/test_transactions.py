import os
import time

import karchive

TEST_NAME = 'test_archive.deleteme.dat'

def test_transaction():
  db = karchive.Database(TEST_NAME, overwrite=True)
  b = db.allocate()
  ar = karchive.Array(db, b, 'I', new=True)

  assert len(ar) == 0

  # ar.append(1)
  # assert len(ar) == 1

  # db.rollback()
  # assert len(ar) == 0

  ar.append(1)
  assert len(ar) == 1
  db.commit()
  assert len(ar) == 1

  ar.close()
  db.close()

  db = karchive.Database(TEST_NAME)
  ar = karchive.Array(db, b, 'I', new=False)
  assert len(ar) == 1
  assert ar.pop() == 1

  ar.close()
  db.close()
  os.remove(TEST_NAME)

