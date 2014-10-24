karchive
========

karchive is an embedded database management system library. It operates
as a library to read and write data structures contained in a single database
file.

[![Build Status](https://travis-ci.org/Knio/karchive.svg?branch=v3)](https://travis-ci.org/Knio/karchive)
[![Coverage Status](https://img.shields.io/coveralls/Knio/karchive.svg)](https://coveralls.io/r/Knio/karchive?branch=v3)

Karchive is:
* Embedded (your application opens the databae file directly)
* Single-user (only one process can open the file at a time)
* ACID complient (supports transactions and guarantees data reliability)
* Efficient (datastructures are fase, all operations do not need to load
    large structures into memory, and )

Karchive is NOT:
* Client-server (you do not connect to a database server)
* SQL (you operate on the database structures directly though a programming API,
    not by writing SQL queries)





Datastructures
==============

karachive supports blobs, lists, and hash tables.

Blobs
-----

A blob is a an arbitrary sized array of bytes. The maximum size of a blob is
slightly less than 4GB. Blobs can be accessed similar to a regular file or a
Python `bytearray`. Indexing a blob (blob[x] = 'a') is efficient and does not
need to load the whole blob data into memory. Blobs can be efficiently appended
to. An empty blob has an overhead of about 12KB on disk (3 pages).

Blob(db) -> Blob object

blob[i] -> byte
blob[j] = y

blob[i:j] -> bytestr
blob[i:j] = x

blob.resize(n) # make blob n bytes long
blob.append(bytestr) # append bytes to end of blob, causing it to grow


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



























