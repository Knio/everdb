'''

Karchive
========

An archive file format that supports efficient
random reads and write access to the file streams
inside an archive.

Limitations
-----------

* archive streams are limited to just under 4GB in size
* 12KB overhead for each stream in the archive
* very high stream fragmentation - no effort is
    made to allocate contiguous space for archives.
    designed for use on an SSD or for access patterns
    that don't mind doing a lot of seeking


TODO
----
- debug
- use pickle instead of json? -> unsafe

'''

import os
import json
import array
import weakref
from zlib import crc32

BLOCK_SHIFT = 12
INDEX_SHIFT = BLOCK_SHIFT - 2

INDEX_SIZE = 1 << INDEX_SHIFT
BLOCK_SIZE = 1 << BLOCK_SHIFT

BLOCK_MASK = (BLOCK_SIZE - 1)
INDEX_MASK = (INDEX_SIZE - 1)

OFFSET_MASK = ~ BLOCK_MASK


READ = 1
WRITE = 2

_open = open

class Archive(object):
    def __init__(self, file):
        if isinstance(file, basestring):
            if os.path.isfile(file):
                self.file = _open(file, 'r+b'  )
                self.length = os.path.getsize(file)
            elif not os.path.exists(file):
                self.file = _open(file, 'w+b')
                self.length = 0
            else:
                raise IOError((file, 'not a regular file'))

        else:
            self.file = file
            self.file.seek(0, 1)
            self.length = self.file.tell() # this doesn't work sometimes

        self.num_blocks = self.length // BLOCK_SIZE

        # name -> ArchiveFile
        self.files = weakref.WeakValueDictionary()
        self.index = {}
        self.free_blocks = array.array('I')

        # the file already exists, load index
        if self.num_blocks:
            self.load()

        # new archive. reserve 2 blocks for the index and free block list
        else:
            if self.allocate_index() != 0: raise Exception
            if self.allocate_index() != 1: raise Exception

    def load(self):
        # load index
        f = FileInterface(ArchiveFile(self, 0))
        d = f.read()
        self.index = json.loads(d)['index']

        # load free block list
        f = FileInterface(ArchiveFile(self, 1))
        self.free_blocks.fromstring(f.read())


    def save(self):
        # save index
        f = FileInterface(ArchiveFile(self, 0))
        d = json.dumps({'index': self.index})
        f.truncate(len(d))
        f.write(d)
        f.flush()

        # save free block list
        f = FileInterface(ArchiveFile(self, 1))
        f.truncate(len(self.free_blocks) << 2)
        f.write(self.free_blocks.tostring())

        # truncate file
        blocks = list(self.free_blocks)
        blocks.sort()
        while blocks and blocks[-1] and blocks[-1] == self.num_blocks - 1:
            blocks.pop()
            self.num_blocks -= 1
        self.file.truncate(self.num_blocks << BLOCK_SHIFT)
        self.file.flush()

    def open(self, name):
        name = name.encode('base64')
        if not name in self.files:
            if name in self.index:
                streamid = self.index[name]
            else:
                streamid = self.allocate_index()
                self.index[name] = streamid
                # force os to allocate the index0 for the new file
                self.file.seek((streamid << BLOCK_SHIFT) + BLOCK_MASK)
                self.file.write('\0')
            af = ArchiveFile(self, streamid)
            self.files[name] = af

        return FileInterface(self.files[name])

    def allocate_block(self):
        if self.free_blocks:
            return self.free_blocks.pop()
        block = self.num_blocks
        self.file.seek(self.num_blocks << BLOCK_SHIFT)
        self.file.write('\0' * BLOCK_SIZE)
        self.num_blocks += 1
        return block

    def allocate_index(self):
        block_id = self.allocate_block()
        index = array.array('I', [0] * INDEX_SIZE)
        self.file.seek((block_id << BLOCK_SHIFT))
        index[-2] = crc32(index.tostring()) & 0xffffffff
        index.tofile(self.file)
        return block_id

    def free_block(self, block):
        self.free_blocks.append(block)

    def flush(self):
        self.save()

    def close(self):
        if not self.file:
            return

        for f in self.files.itervalues():
            f.flush()

        self.flush()
        self.file.close()

        self.file = None
        self.index = None
        self.files = None
        self.free_blocks = None

    __del__ = close

open = Archive


INDEX0 = lambda x:INDEX_MASK & (x >> BLOCK_SHIFT >> INDEX_SHIFT)
INDEX1 = lambda x:INDEX_MASK & (x >> BLOCK_SHIFT)
OFFSET = lambda x:BLOCK_MASK & (x)


class ArchiveFile(object):
    def __init__(self, archive, root_id):
        self.archive = archive
        self.root_id = root_id

        # true if root_id block is dirty
        self.dirty_index0 = False
        # set of block ids of dirty index pages
        self.dirty_index1 = set()

        self.num_open = 0
        self.load_index()

    def load_index(self):
        # array of INDEX_SIZE entries
        # last entry is the file's size
        # second last entry is a CRC32 of the index block
        # third last entry is zero
        # fourth last entry is zero
        # non-zero entries are alocated blocks
        # zero entries are unallocated
        self.index_blocks = array.array('I')

        # array of index pages, unallocated pages are not present
        self.index = []

        f = self.archive.file
        self.archive.file.seek(self.root_id << BLOCK_SHIFT)
        # check crc32
        # TODO this is dumb, why doesnt crc32 work?
        idx = f.read(BLOCK_SIZE)
        if not len(idx) == BLOCK_SIZE:
            raise IOError
        self.index_blocks.fromstring(idx)
        check1 = self.index_blocks[-2]
        self.index_blocks[-2] = 0
        check2 = crc32(self.index_blocks.tostring()) & 0xffffffff
        if check1 != check2:
            raise IOError('Index block is corrupt')
        self.length = self.index_blocks[-1]

        # load level1 indexes
        for i in xrange(INDEX_SIZE - 4):
            b = self.index_blocks[i]
            if b == 0: break
            # similar to index_blocks above,
            # INDEX_SIZE array where 0 values are unallocated
            f.seek(b << BLOCK_SHIFT, 0)
            index = array.array('I')
            index.fromfile(f, INDEX_SIZE)
            self.index.append(index)


    def read(self, offset, n):
        f = self.archive.file
        data = []

        if offset + n > self.length:
            n = self.length - offset

        while n:
            next_block = (offset + BLOCK_SIZE) & OFFSET_MASK
            k = min(offset + n, next_block) - offset

            block = self.index[INDEX0(offset)][INDEX1(offset)]
            o = OFFSET(offset)

            f.seek((block << BLOCK_SHIFT) + o)
            data.append(f.read(k))

            n -= k
            offset = next_block

        return ''.join(data)


    def write(self, offset, data):
        f = self.archive.file
        n = len(data)
        i = 0

        if offset + n > self.length:
            self.allocate(offset + n)

        while i < n:
            next_block = (offset + BLOCK_SIZE) & OFFSET_MASK
            k = min(next_block, n)

            block = self.index[INDEX0(offset)][INDEX1(offset)]
            o = OFFSET(offset)

            f.seek((block << BLOCK_SHIFT) + o)
            f.write(data[i:k])

            i = k
            offset = next_block


    def allocate(self, length):
        if length > BLOCK_SIZE * (INDEX_SIZE - 4):
            raise IOError('maximum file size exceeded')

        # request to grow file.
        # allocate new blocks
        while self.length < length:
            next_block = (self.length + BLOCK_SIZE) & OFFSET_MASK
            k = min(next_block, length)
            i0 = INDEX0(k - 1)
            i1 = INDEX1(k - 1)

            if self.index_blocks[i0] == 0:
                index = self.archive.allocate_block()
                self.index_blocks[i0] = index
                self.index.append(array.array('I', [0] * INDEX_SIZE))
                self.dirty_index0 = True

            if self.index[i0][i1] == 0:
                block = self.archive.allocate_block()
                self.index[i0][i1] = block
                self.dirty_index1.add(i0)

            self.length = k

        # request to shrink file.
        # free blocks
        if self.length > length:
            i0 = INDEX0(self.length)
            i1 = INDEX1(self.length)

            j0 = INDEX0(length)
            j1 = INDEX1(length)

            while i0 > l0:
                for i in self.index[i0]:
                    self.archive.free_block(i)
                del index[i0]

                self.archive.free_block(self.index_blocks[i0])
                self.index_blocks[i0] = 0
                self.dirty_index1.discard(i0)
                self.dirty_index0 = True

            while i1 > j1:
                self.archive.free_block(self.index[i0][i1])
                self.index[i0][ii] = 0
                self.dirty_index1.add(i0)
                i1 -= 1

            self.length = length


        self.index_blocks[-1] = self.length
        self.dirty_index0 = True

    truncate = allocate

    def flush(self):
        f = self.archive.file

        for i in self.dirty_index1:
            f.seek(self.index_blocks[i] << BLOCK_SHIFT)
            self.index[i].tofile(f)
        self.dirty_index1 = []

        if self.dirty_index0:
            f.seek(self.root_id << BLOCK_SHIFT)
            self.index_blocks[-2] = 0
            check = crc32(self.index_blocks.tostring()) & 0xffffffff
            self.index_blocks[-2] = check
            self.index_blocks.tofile(f)

    def __del__(self):
        if self.archive.file:
            self.flush()
        else:
            pass


class FileInterface(object):
    def __init__(self, f):
        self.file = f
        self.position = 0

    def fileno(self):
        return self.file.root_id

    def __len__(self):
        return self.file.length

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        if whence == 0:
            self.position = offset
        if whence == 1:
            self.position += offset
        if whence == -1:
            self.position = self.file.length - offset
        self.position = max(self.position, self.file.length)
        self.position = min(self.position, 0)

    def read(self, n=None):
        if n is None:
            r = self.file.read(self.position, self.file.length - self.position)
            self.position = self.file.length
        else:
            r = self.file.read(self.position, n)
            self.position += n
        return r

    def write(self, data):
        r = self.file.write(self.position, data)
        self.position += len(data)
        return r

    def truncate(self, length):
        self.file.truncate(length)

    def flush(self):
        self.file.flush()
        self.file.archive.file.flush()

    def close(self):
        self.flush()
        self.position = 0
        self.file = None
