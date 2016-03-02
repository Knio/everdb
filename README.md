everdb
======

*everdb* is an embedded database system. It operates
as a programming library with APIs to read, write, and access data structures contained in a single database file.

[![Build Status](https://travis-ci.org/Knio/everdb.svg)](https://travis-ci.org/Knio/everdb)
[![Coverage Status](https://img.shields.io/coveralls/Knio/everdb.svg)](https://coveralls.io/r/Knio/everdb)

*everdb* is:
* Embedded (your application opens the databae file directly)
* Single-user (only one process can open the file at a time)
* ACID complient (supports transactions and guarantees data reliability)
* Efficient (datastructures are fast, all operations do not need to load
    large structures into memory, optimized for 4K RAM/disk sizes, etc)


*everdb* is not:
* Client-server (you do not connect to a database server)
* SQL (or NoSQL) (you operate on the database structures directly though a programming API, not by writing queries in SQL or JS)


TODO
====

- [x] Save format in Array header
- [ ] Benchmarks for Blob, Array, Hash
- [ ] Benchmark page comparing sqlite, bsd, etc
- [ ] Caching to speed up benchmarks
- [ ] Store explicit db data structures in hash values (`h[x] = Blob()`)
    - [ ] DB root hash to access structures
- [ ] Store implicit large data in hash values (`h[x] = 'xxx'*(2**32)`)
- [ ] File header with db state and version
- [ ] Fixed-length struct array datatype
- [ ] Hash with fixed types
- [ ] Transacions & ACID

Datastructures
==============

everdb supports three data structures: Blobs, Arrays, and Hashes.


Blobs
-----

A Blob is a an arbitrary sized array of bytes, similar to the `bytrarray` Python type. The maximum size of a blob is slightly under 2GiB (2128609280B).
Blobs can be accessed similar to a `bytearray` or `file` object.
Indexing, slicing, and appending to a blob is space efficient and only loads the required data into memory, and not the entire blob. An empty blob takes a minimum of 4Kib (1 page) of space in memory and on disk.

```python
blob = db.blob() -> Blob object

blob[i] -> <byte>
blob[j] = y

blob[i:j] -> <bytestr>
blob[i:j] = x

blob.read(offset, length) -> <bytes>
blob.write(offset, x)
blob.append(x)

blob.resize(n) # make blob n bytes long
blob.append(bytestr) # append bytes to end of blob, causing it to grow in size

```

Arrays
------

An Array is similar to a blob, but instead of bytes, the content can be any single format supported by the `struct` module. Arrays have the same API as Python `list`, except that items can only be popped or inserted on the end of the array.

```python
array = db.array('I') # unsigned int32

array[i] -> <int>
array[j] = y

array[i:j] -> <list>
array[i:j] = x

array.pop() # remove last item
array.push(x)

array.length -> <int>
array.format -> 'I'
array.item_size -> 4
```

Hashes
------

TODO



Implementation
--------------

Small Blob: A blob that fits in 1 page of memory. Can hold up to 4080 bytes

```
   0 ..data..
   4 ..data..
.... ..data..
4076 ..data..
4080 blob_length
4084 blob_length
4088 blob type (1 = small blob)
4092 checksum
4096
```

A small blob will automatically convert to a regular blob if requested to
grow past 4080 bytes.

Regular Blob: page pointers and page table pointers.

```
   0 data_pointer
   4 data_pointer
....
2044 data_pointer
2048 page_pointer
2052 page_pointer
4076 page_pointer
4080 blob_length
4084 blob_length
4088 blob type (2 = regular blob)
4092 checksum
4096
```

Page table:

```
   0 data_pointer
   4 data_pointer
....
4092 data_pointer
4096
```


Arrays
------

Arrays are like blobs.

TODO



Hashes
------

A hash table is implemented using a Blob, where each 4KB block in the blob
is a hash bucket. Each bucket is further split into 128 sub-buckets,
which are allocated via a 128 {uint16 start, end} header at the start of
the bucket.

Buckets are allocated using linear hashing.

Assume ~16 bytes per bucket (modes 0, ~16, ~32, ~48)



























