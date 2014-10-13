import msgpack

from .blob import Blob
from .blob import BLOCK_SIZE
from .blob import SMALL_BLOB, REGULAR_BLOB

'''
Linear hash table

hash table contains N (num_blocks) buckets,
with parameters L (level) and S (split).

2**L is the largest power of 2 not greater than N,
and 2**(L+1) is the next power of 2 that we are resizing the hash into

0 <= 2**L <= N < 2**(L+1)
0 <= S < 2**L
thus:
S <= 2*N

To resize the hash table, we split the bucket with index S into new locations
S and 2*S. We re-hash the items in bucket S with hash function H % (2**(L+1)),
and are guaranteed that the result will be <= N becase the origial hash function
result was S

Example:

Hash table of 4 buckets:

N=4
L=2
S=0

To grow the hash table by one bucket:
Allocate a new bucket, so N=5

split bucket S, and re-hash the items into buckets S and 2**L + S (= new bucket)
increment S by 1


'''


class Hash(Blob):

  HEADER = dict((k, i) for i, k in enumerate([
    'size',
    'split',
    'level',
    'num_blocks',
    'type',
    'checksum', # must be last
  ]))

  def __init__(self, host, root, new):
    super(Hash, self).__init__(host, root, new)

  def init_root(self):
    self.step = 0
    self.level = 0
    super(Hash, self).init_root()
    data = msgpack.dumps({})
    self.resize(len(data))
    self.write(0, data)
    self.flush_root()

  def get_bucket(self, key):
    h = hash(key)
    b = h & ((1 << self.level) - 1)
    if b < self.split:
      b = h & ((2 << self.level) - 1)

    if self.num_blocks == 0:
      blob = self
    else:
      blob = Blob(self.host, self.get_host_index(b), False)
    data = blob.read()

    bucket = msgpack.loads(data)
    return b, blob, bucket

  def get(self, key):
    b, blob, bucket = self.get_bucket(key)
    return bucket[key]

  def set(self, key, value):
    b, blob, bucket = self.get_bucket(key)
    if key not in bucket:
      self.size += 1
      self.set_checksum()

    bucket[key] = value
    data = msgpack.dumps(bucket)
    blob.resize(len(data))
    blob.write(0, data)

    if len(data) > 3072:
      self.grow()

    self.verify_checksum()

  def delete(self, key):
    raise NotImplementedError

  __getitem__ = get
  __setitem__ = set
  __delitem__ = delete

  def __len__(self):
    return self.size

  def grow(self):
    s = self.split

    if self.num_blocks == 0:
      data = self.read()
      self.type = REGULAR_BLOB
      # TODO zero data?
      self.allocate(2)
      b0 = Blob(self.host, self.get_host_index(s), True)

    else:
      self.allocate(self.num_blocks + 1)
      b0 = Blob(self.host, self.get_host_index(s), False)
      data = b0.read()

    b1 = Blob(self.host, self.get_host_index(s + (1 << self.level)), True)

    bucket = msgpack.loads(data)

    bucket0 = {}
    bucket1 = {}
    for k, v in bucket.items():
      h = hash(k)
      b = h & ((2 << self.level) - 1)
      if b == s:
        bucket0[k] = v
      elif b == (s + (1 << self.level)):
        bucket1[k] = v
      else:
        assert False, b

    data0 = msgpack.dumps(bucket0)
    b0.resize(len(data0))
    b0.write(0, data0)

    data1 = msgpack.dumps(bucket1)
    b1.resize(len(data1))
    b1.write(0, data1)

    if s + 1 == (1 << self.level):
      self.level += 1
      self.split = 0

    else:
      self.split += 1

    self.set_checksum()
