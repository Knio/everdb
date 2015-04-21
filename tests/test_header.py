import zlib
import struct

from everdb.header import Header, Field

class Foo(Header):
  foo = Field('Q')

class Bar(Foo):
  bar = Field('B')
  baz = Field('B')

def test_header():
  assert Foo._header == [
    ('foo', 'Q'),
  ]

  assert Foo._header_fmt == '!Q'
  assert Foo._header_size == 12


  assert Bar._header == [
    ('bar', 'B'),
    ('baz', 'B'),
    ('foo', 'Q'),
  ]
  assert Bar._header_fmt == '!BBQ'
  assert Bar._header_size == 14

  by = b'sdfsdfsdfsdfsdfsdf'
  by += struct.pack('I', zlib.crc32(by))
  by = bytearray(by)
  mv = memoryview(by)

  b = Bar()
  b.load_header(mv)
  assert b.foo == 7234596726470042726
  assert b.baz == 115
  assert b.bar == 102

  b.foo = 102030405
  b.bar = 74
  b.baz = 1

  b.sync_header(mv)

  b.load_header(mv)
  assert b.foo == 102030405
  assert b.bar == 74


if __name__ == '__main__':
  test_header()
