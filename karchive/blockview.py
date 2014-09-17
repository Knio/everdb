# pylint: disable=missing-docstring, W0311, invalid-name

class BlockView(object):
  def __init__(self, host, block, format='B'):
    self.host = host
    self.block = block
    self.format = format
    self._old_block = block
    self._dirty = False
    self._view = None

  def release(self):
    if not self._view: return
    self._view.release()
    self._view = None

  def get_view(self):
    if self._view: return
    self._view = self.host.get_block(self.block).cast(self.format)
    self.host.add_blockview(self)

  def make_dirty(self):
    if self._dirty: return
    self._dirty = True
    self.release()
    new_block = self.host.allocate()
    self.host.set_block(new_block,
        self.host.get_block(self._old_block))
    self.block = new_block

  def commit(self):
    self.host.flush(self.block)
    self.host.free(self._old_block)
    self._old_block = self.block
    self._dirty = False

  def rollback(self):
    if not self._dirty: return
    self._dirty = False
    self.release()
    self.host.free(self.block)
    self.block = self._old_block

  def __getitem__(self, i):
    if not self._view:
      self.get_view()
    return self._view[i]

  def __setitem__(self, i, v):
    if not self._dirty:
      self.make_dirty()
    if not self._view:
      self.get_view()
    self._view[i] = v
