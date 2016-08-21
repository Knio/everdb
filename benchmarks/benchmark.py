from collections import defaultdict
import cProfile as profile
import itertools
import os
import pstats
import sys
import time

class Benchmark(object):
  def __init__(self):
    pass

  def setup(self):
    pass

  def run(self, n):
    pass

  def teardown(self):
    pass

  def benchmark(self, n=100000):
    self.setup(n)
    try:
      start_time = time.time()
      self.run(n)
      end_time = time.time()
    finally:
      self.teardown()

    duration = end_time - start_time
    return duration

  def bench(self):
    T = 0.40
    n = 1000
    d = 0
    while 1:
      d = self.benchmark(n)
      # print((n,d))
      if d > T: break
      n = int(1.5 * T * n / (d + 0.0005))

    print('    %-10s%6d ops/ms' % (
        type(self).__name__.split('Benchmark')[1],
        float(n)/d/1000
    ))

  def profile(self, n=10000):
    pr = profile.Profile()

    self.setup(n)
    try:
      pr.enable()
      self.run(n)
      pr.disable()
    finally:
      self.teardown()

    ps = pstats.Stats(pr).sort_stats('cumulative')
    print('    %-10s' % type(self).__name__.split('Benchmark')[1])
    ps.print_stats(10)


def main():
  args = sys.argv[1:]
  if not len(args) >= 1:
    print('Usage:'
      'benchmark.py command [name]')
    sys.exit(1)
  cmd = args.pop(0)

  filter_name = None
  if args:
    filter_name = args.pop(0)

  classes = {n:c for n,c in globals().items() if \
      type(c) == type and c.__bases__ == (Benchmark,)}

  benchmarks = defaultdict(dict)
  for n, c in classes.items():
    benchmarks[n.split('Benchmark')[0]][n] = c

  for name, bm in sorted(benchmarks.items()):
    if filter_name and filter_name != name: continue
    print()
    print(name)
    for n, b in sorted(bm.items()):
      f = getattr(b(), cmd)
      f()



TEST_NAME = '_everdb.test.deleteme'
import everdb
import sqlite3

class ArrayAppendBenchmarkEverdb(Benchmark):
  def setup(self, n):
    self.db = everdb.open(TEST_NAME, overwrite=True)
    self.ar = self.db.array('I')

  def run(self, n):
    ar = self.ar
    for i in range(n):
      ar.append(i)
    ar.flush()

  def teardown(self):
    self.ar.close()
    self.db.close()
    os.remove(TEST_NAME)


class ArrayAppendBenchmarkList(Benchmark):
  def setup(self, n):
    self.ar = []

  def run(self, n):
    ar = self.ar
    for i in range(n):
      ar.append(i)

  def teardown(self):
    self.ar[:] = []


class ArrayAppendBenchmarkSqlite(Benchmark):
  def setup(self, n):
    self.db = sqlite3.connect(TEST_NAME + '.sql')
    self.c = self.db.cursor()
    self.c.execute('''create table ar (v integer)''')

  def run(self, n):
    c = self.c
    for i in range(n):
      c.execute('insert into ar values (?)', (i,))
    self.db.commit()

  def teardown(self):
    self.c.close()
    self.db.close()
    os.remove(TEST_NAME + '.sql')


class ArrayIterateBenchmarkList(Benchmark):
  def setup(self, n):
    self.ar = list(range(n))

  def run(self, n):
    ar = self.ar
    for i in range(n):
      x = ar[i]

  def teardown(self):
    self.ar[:] = []


class ArrayIterateBenchmarkEverdb(Benchmark):
  def setup(self, n):
    self.db = everdb.open(TEST_NAME, overwrite=True)
    self.ar = ar = self.db.array('I')
    for i in range(n):
      ar.append(i)

  def run(self, n):
    ar = self.ar
    for i in range(n):
      x = ar[i]

  def teardown(self):
    self.ar.close()
    self.db.close()
    os.remove(TEST_NAME)


class ArrayIterateBenchmarkSqlite(Benchmark):
  def setup(self, n):
    self.db = sqlite3.connect(TEST_NAME + '.sql')
    self.c = c = self.db.cursor()
    self.c.execute('''create table ar (i integer, v integer)''')
    self.c.execute('''create index i_ar on ar (i)''')
    for i in range(n):
      c.execute('insert into ar values (?, ?)', (i,i))
    self.db.commit()

  def run(self, n):
    c = self.c
    for i in range(n):
      c.execute('select v from ar where i = ?', (i,))
      x = c.fetchone()[0]

  def teardown(self):
    self.c.close()
    self.db.close()
    os.remove(TEST_NAME + '.sql')


class ArrayPopBenchmarkEverdb(Benchmark):
  def setup(self, n):
    self.db = everdb.open(TEST_NAME, overwrite=True)
    self.ar = ar = self.db.array('I')
    for i in range(n):
      ar.append(i)

  def run(self, n):
    ar = self.ar
    for i in range(n):
      x = ar.pop()
    ar.flush()

  def teardown(self):
    self.ar.close()
    self.db.close()
    os.remove(TEST_NAME)


class ArrayPopBenchmarkSqlite(Benchmark):
  def setup(self, n):
    self.db = sqlite3.connect(TEST_NAME + '.sql')
    self.c = c = self.db.cursor()
    self.c.execute('''create table ar (i integer, v integer)''')
    self.c.execute('''create index i_ar on ar (i)''')
    for i in range(n):
      c.execute('insert into ar values (?, ?)', (i,i))
    self.db.commit()

  def run(self, n):
    c = self.c
    for i in range(n):
      c.execute('select v from ar where i = ?', (i,))
      x = c.fetchone()[0]
      c.execute('delete from ar where i = ?', (i,))
    self.db.commit()

  def teardown(self):
    self.c.close()
    self.db.close()
    os.remove(TEST_NAME + '.sql')


class ArrayPopBenchmarkList(Benchmark):
  def setup(self, n):
    self.ar = list(range(n))

  def run(self, n):
    ar = self.ar
    for i in range(n):
      ar.pop()

  def teardown(self):
    self.ar[:] = []


class HashInsertBenchmarkEverdb(Benchmark):
  def setup(self, n):
    self.db = everdb.open(TEST_NAME, overwrite=True)
    self.hs = self.db.hash()

  def run(self, n):
    hs = self.hs
    for i in range(n):
      hs[i] = i
    hs.flush()

  def teardown(self):
    self.hs.close()
    self.db.close()
    os.remove(TEST_NAME)


class HashInsertBenchmarkDict(Benchmark):
  def setup(self, n):
    self.hs = {}

  def run(self, n):
    hs = self.hs
    for i in range(n):
      hs[i] = i

  def teardown(self):
    self.hs.clear()




if __name__ == '__main__':
  main()
