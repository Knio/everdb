everdb
======

*everdb* is an embedded database system. It operates as a programming library
with APIs to read, write, and access various on-disk data structures contained in a single regular file.

*everdb* is currently in experemental development and is not fit for use. Please check back later for a working product.

*everdb* currently has two implmementations: 
 - [everdb-python](https://github.com/Knio/everdb-python)
 - [everdb-native](https://github.com/Knio/everdb-native)

### Python
[![Build Status][buildlogo-python]](https://travis-ci.org/Knio/everdb-python)
[![Coverage Status][coveragelogo-python]](https://coveralls.io/r/Knio/everdb-python)

[buildlogo-python]: https://travis-ci.org/Knio/everdb-python.svg?branch=master
[coveragelogo-python]: https://img.shields.io/coveralls/Knio/everdb-python.svg?branch=master

### C

[![Build Status][buildlogo-native]](https://travis-ci.org/Knio/everdb-native)
[![Coverage Status][coveragelogo-native]](https://coveralls.io/r/Knio/everdb-native)

[buildlogo-native]: https://travis-ci.org/Knio/everdb-native.svg?branch=master
[coveragelogo-native]: https://img.shields.io/coveralls/Knio/everdb-native.svg?branch=master


## What is it for?


*everdb* is:
* Embedded (your application opens the database file directly)
* Single-user (only one process can open the file at a time)
* ACID compliant (supports transactions and guarantees data reliability)
* Efficient (datastructures are fast, all operations do not need to load large
  structures into memory, optimized for 4K RAM/disk sizes, etc)

*everdb* is not:
* Client-server (you do not connect to a database server)
* SQL (or NoSQL) (you operate on the database structures directly though a
  programming API, not by writing queries in SQL or JS)


## Supported Data Structures

*everdb* currently has planned support for the following data structures:
 - *blobs*
 - *arrays*
 - *hashes*

Likely future additions include:
- btrees
- log structured merge trees
- judy arrays
- etc..


### blobs

A *blob* is a an arbitrary sized array of bytes. *blobs* support time and memort efficient random read, overwrite, and append in `O(n)` of the requested data (and not the total blob size, so you can efficiently append a single byte to a huge blob).

#### Limitations
- an empty blob uses 1 page (4KiB) of data in the database file
- a blob cannot exceed 2128609280 bytes (slightly under 2GiB)

Python example:
```python
>>> blob = db.blob()
<Blob object>
>>> blob[i]
b"X"
>>> blob[j] = "Y"
>>> blob[i:j]
b"Hello World"
>>> blob[i:j] = "01234 56789"
>>> blob.read(offset, length)
b"Hello World"
>>> blob.write(offset, x)
>>> blob.append(x)
>>> blob.resize(n) # make blob n bytes long
```


### arrays

An *array* is similar to a *blob*, but instead of bytes, the content can be a multi-byte type. In Python, this can be any format supported by the `struct` module, and in C this can be any struct. Arrays have the same API as blobs, except can only access single elements at a time

#### Limitations
In addition to the limits of *blob*:
- the size of a single element in the array cannot exceed 1 page (4KiB)
- if the size of a single element does not evenly divide 4KiB, there will be 4KiB % sizeof(type) wasted space per page of array data

Python Example:
```python
>>> array = db.array('IIHf')
>>> array[i]
(1, 2, 3, 4.0)
>>> array[j] = (5, 6, 7, 8.9)
>>> array.length
1
>>> array.format
'IIHd'
array.item_size
14
```


### hashes

*hashes* are key-value stores where both the key and values are arbitrary-length byte arrays.

TODO
