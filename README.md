karchive
========

karchive is an embedded database management system library. It operates
as a library to read and write data structures contained in a single database
file.


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

blob.append(bytestr)
blob.truncate(i)


Arrays
------

Arrays are like blobs, but































