# pylint: disable=W0311

import struct
import zlib

CRC32_MAGIC = 558161692

class Field(str): pass

class HeaderMeta(type):
  def __init__(cls, name, bases, dct):
    super(HeaderMeta, cls).__init__(name, bases, dct)
    h = sorted(
      [(k, v) for k,v in dct.items() if isinstance(v, Field)],
      key=lambda x:(struct.calcsize(x[1]), x[0]))

    for b in bases:
      n = getattr(b, '_header', None)
      if n:
        h.extend(n)
        break

    if h:
      cls._header = h
      cls._header_names = list(zip(*h))[0]
      cls._header_fmt = '!' + ''.join(list(zip(*h))[1])
      cls._header_size = struct.calcsize(cls._header_fmt) + 4


HeaderBase = HeaderMeta('HeaderBase', (object,), {})

class Header(HeaderBase):

  def load_header(self, mv):
    m = mv.cast('B')
    if zlib.crc32(m) != CRC32_MAGIC:
      raise ValueError('Checksum error')
    s = struct.unpack_from(self._header_fmt, mv, len(mv) - self._header_size)
    for k, v in zip(self._header_names, s):
      setattr(self, k, v)

  def sync_header(self, mv):
    m = mv.cast('B')
    v = [getattr(self, k) for k in self._header_names]
    struct.pack_into(self._header_fmt, m, len(m) - self._header_size, *v)
    struct.pack_into('@I', m, len(m) - 4, zlib.crc32(m[0:-4]))
