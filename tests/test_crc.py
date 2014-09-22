import zlib
import struct

def test_crc():
    d1 = b'aks ldf jkl asd jfk lsax'
    c1 = zlib.crc32(d1)
    d2 = d1 + struct.pack('<I', c1)
    c2 = zlib.crc32(d2)
    assert c2 == 558161692

