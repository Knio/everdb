import os
import sys
import time
import cProfile as profile
import pstats

import everdb
import sqlite3

TEST_NAME = 'test_archive.deleteme.dat'


def bench_list_append():
  ar = []
  N = 1000000
  start_time = time.time()
  for i in range(N):
    ar.append(i)
  duration = time.time() - start_time
  print('append %d in %dms (%d us/item)' %
      (N, 1000 * duration, 1000000 * duration/N))


def bench_append():
  db = everdb.open(TEST_NAME, overwrite=True)
  ar = db.array('I')

  N = 100000
  start_time = time.time()
  for i in range(N):
    ar.append(i)
  ar.flush()
  print(ar)
  duration = time.time() - start_time
  print('append %d in %dms (%d us/item)' %
      (N, 1000 * duration, 1000000 * duration/N))



def bench_sqlite_append():
  try:
    os.remove(TEST_NAME + '.sql')
  except:
    pass
  db = sqlite3.connect(TEST_NAME + '.sql')
  c = db.cursor()
  c.execute('''create table ar (v integer)''')

  N = 100000
  start_time = time.time()
  for i in range(N):
    c.execute('insert into ar values (?)', (i,))
  # c.flush()
  # print(ar)
  duration = time.time() - start_time
  print('append %d in %dms (%d us/item)' %
      (N, 1000 * duration, 1000000 * duration/N))



def prof_append():
  pr = profile.Profile()
  # for i in range(5):
  #   pr.calibrate(10000)

  db = everdb.open(TEST_NAME, overwrite=True)
  ar = db.array('I')

  N = 100000

  pr.enable()
  for i in range(N):
    ar.append(i)
  pr.disable()

  ar.flush()
  print(ar)
  ps = pstats.Stats(pr).sort_stats('cumulative')
  ps.print_stats()


if __name__ == '__main__':
  args = sys.argv[1:]
  if args[0] == 'bench':
    bench_append()
  elif args[0] == 'prof':
    prof_append()
  elif args[0] == 'list':
    bench_list_append()
  elif args[0] == 'sql':
    bench_sqlite_append()



