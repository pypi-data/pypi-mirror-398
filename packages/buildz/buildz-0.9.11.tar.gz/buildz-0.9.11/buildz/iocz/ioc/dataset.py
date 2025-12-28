#

from .tdata import TagData
from .base import *
from ... import dz
class Dataset(Base):
    '''
        所有数据集，只包含pub和ns部分
    '''
    def str(self):
        return f"Dataset(pub={self.pub}, ns={self.ns})"
    def init(self, ids):
        self.ids = ids
        self.pub = {}
        self.ns = {}
        self.objs = {}
    def update(self, maps, ns=None, tag=None, id=None, flush=False):
        if flush:
            maps = dz.unflush_maps(maps, self.ids.id)
        for key, val in maps.items():
            self.set(key, val, ns, tag, id)
    def set(self, key, val, ns=None, tag=None, id=None):
        if tag == TagData.Key.Ns:
            self.ns_set(key,val,ns,id)
        else:
            self.pub_set(key,val,ns,id)
    def pub_set(self, key, val, ns=None, id=None):
        keys = self.ids(ns)+self.ids(key)
        dz.dset(self.pub, keys, val)
    def ns_set(self, key, val, ns=None, id=None):
        map = dz.get_set(self.ns, ns, dict())
        dz.dset(map, self.ids(key),val)
        #map[key] = val
    def add(self, data):
        ns = data.ns
        self.objs[data.id] = data
        for key, val in data.tag(data.Key.Pub).items():
            self.pub_set(key, val, ns, data)
        for key, val in data.tag(data.Key.Ns).items():
            self.ns_set(key, val, ns, data)
        if data.dts!=self:
            data.bind(self)
    def tget(self, key, ns=None, tag=None, id=None):
        obj, keys,tag, find = self.get(key,ns,tag, id)
        return obj, tag, find
    def get(self, key, ns=None, tag=None, id = None):
        keys = self.ids(key)
        if len(keys)==0:
            return None,None,None,0
        if tag == TagData.Key.Pub:
            find =False
        else:
            obj, find = self.ns_get(key,ns,id)
            tag = TagData.Key.Ns
            keys = key
        if not find:
            obj, keys, find=self.pub_get(key,ns,id)
            tag=TagData.Key.Pub
        return obj,keys,tag,find
    def _pub_get(self, key, ns=None, id=None):
        ids_key = self.ids(key)
        ids = ids_key
        obj,find = dz.dget(self.pub, ids)
        if find:
            return obj, ids, find
        if ns is None:
            return 0,0, 0
        ids = self.ids(ns) + ids_key
        obj,find = dz.dget(self.pub, ids)
        if find:
            return obj, ids, find
        return None,0,0
    def pub_get(self, key, ns=None, id=None):
        obj,keys,find = self._pub_get(key, ns, id)
        if find:
            return obj,keys,find
        return None,None,0
    def ns_get(self, key, ns=None, id=None):
        map = dz.get_set(self.ns, ns, dict())
        obj, find = dz.dget(map, self.ids(key))
        if not find:
            return None,0
        return obj,1
