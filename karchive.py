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


'''

import array

BLOCK_SHIFT = 12
INDEX_SHIFT = 10

INDEX_SIZE = 1 << INDEX_SHIFT
BLOCK_SIZE = 1 << BLOCK_SHIFT

BLOCK_MASK = (BLOCK_SIZE - 1)
INDEX_MASK = (INDEX_SIZE - 1)

OFFSET_MASK = ~ BLOCK_MASK

class Archive(object):
    def __init__(self, filename):
        self.filename = filename
        self.length = os.getsize(filename)
        self.file = open(filename, 'a+b')
        self.index = ArchiveFile(self, 0)
        self.num_blocks = self.length / BLOCK_SIZE

    def open(self, name, mode):
        if mode == 'r':
            streamid, length = self.index.[name]
        return File(self, streamid, length)

    def allocate_block(self):
        self.file.seek(self.num_blocks * BLOCK_SIZE)
        self.num_blocks += 1
        return self.num_blocks

    def free_block(self, block):
        pass


INDEX0 = lambda x:INDEX_MASK & (x >> BLOCK_SHIFT >> INDEX_SHIFT)
INDEX1 = lambda x:INDEX_MASK & (x >> BLOCK_SHIFT)
OFFSET = lambda x:BLOCK_MASK & (x)


class ArchiveFile(object):
    def __init__(self, archive, root_id):
        self.archive = archive
        self.root_id = root_id

        self.dirty_index0 = False
        self.dirty_index1 = []

        self.load_index()

    def load_index(self):
        self.index_blocks = array.array('I')
        self.index = []

        f = self.archive.file
        self.archive.file.seek(self.root_id << BLOCK_SHIFT)
        self.index_blocks.fromfile(f, INDEX_SIZE)

        for i, b in enumerate(self.index_blocks):
            if b == 0: break
            f.seek(i << BLOCK_SHIFT)
            index = array.array('I')
            index.fromfile(f, BLOCK_SIZE>>2)
            self.index.append(index)

        self.length = self.index_blocks[-1]

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

        self.allocate(offset + n)

        while i < n:
            next_block = (offset + BLOCK_SIZE) & BLOCK_MASK
            k = min(next_block, n) - offset

            block = self.index[INDEX0(offset)][INDEX1(offset)]
            o = OFFSET(offset)

            f.seek((block << BLOCK_SHIFT) + o)
            f.write(data[i:k])

            i = k
            offset = next_block

    def allocate(self, length):
        if self.length >= length:
            # TODO truncate file!
            return

        if length > BLOCK_SIZE * (INDEX_SIZE - 2):
            raise IOError('maximum file size exceeded')

        while self.length < length:
            next_block = (self.length + BLOCK_SIZE - 1) & BLOCK_MASK
            k = min(next_block, length)
            i0 = INDEX0(k)
            i1 = INDEX1(k)

            if self.index_blocks[i0] == 0:
                index = self.archive.allocate_block()
                self.index_blocks[i0] = index
                self.index[i0] = array.array('I', [0] * INDEX_SIZE)
                self.dirty_blocks.append(index)

            if self.index_blocks[i0][i1] == 0:
                block = self.archive.allocate_block()
                self.index_blocks[i0][i1] = block
                self.dirty_index1.append(i0)

            self.length = k

        self.index_blocks[-1] = self.length
        self.dirty_index0 = True

    def truncate(self, length):
        raise NotImplementedError

    def flush(self):
        f = self.archive.file

        if self.dirty_index0:
            f.seek(self.root_id << BLOCK_SHIFT)
            self.index_blocks.tofile(f)

        for i in self.dirty_index1:
            f.seek(i << BLOCK_SHIFT)
            self.index[i].tofile(f)
        self.dirty_index1 = []


class FileInterface(object):
    def __init__(self, f):
        self.file = f
        self.position = 0

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        if whence == 0:
            self.position = offset
        if whence == 1:
            self.position += offset
        if whence == -1:
            self.position = self.length - offset

    def read(self, n=None):
        if n is None:
            return self.f.read(self.position, self.length - self.position)
        else:
            return self.f.read(self.position, n)

    def write(self, data):
        return self.f.write(self.position, data)

    def flush(self):
        self.file.flush()
        self.archive.file.flush()

    def close(self):
        self.flush()
