
class FileObjectMixin(object):
  def get_blocks(self, offset, length):
    '''
    Returns list of (block, offset, length)] ranges.
    blocks are host block ids
    '''
    raise NotImplementedError

  def read(self, offset, length):
    r = []
    for b, o, l in self.get_blocks(offset, length):
      r.append(self.host[b][o:o+l])
    return b''.join(r)

  def write(self, offset, data):
    i = 0
    for b, o, l in self.get_blocks(offset, len(data)):
      self.host[b][o:o+l] = data[i:i+l]
      i += l
