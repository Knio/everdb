# pylint: disable=bad-indentation

import msgpack
import structpack as sp

class BTree(object):
  def __init__(self, host, root):
    self.host = host
    self.root = root

  def __getitem__(self, key):
    node = bt_internal_node.load(self.host[self.root])

    for en in node.data
    while i < len(node.data) and key < node.data[i].key:
      i += 1

    if i == 0:
      raise KeyError




  def __setitem__(self, key, value):
    pass

  def __delitem__(self, key):
    pass


class bt_entry(sp.msg):
  key     = sp.value
  value   = sp.value

class bt_node(sp.msg):
  parent  = sp.int
  left    = sp.int
  right   = sp.int
  data = sp.list(bt_entry)

class bt_leaf_node(bt_node):
  pass

class bt_internal_node(bt_node):
  pass


