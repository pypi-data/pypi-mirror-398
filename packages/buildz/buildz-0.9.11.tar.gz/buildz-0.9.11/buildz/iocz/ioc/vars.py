#
from .tdata import TagData
from .datas import Datas
from .dataset import Dataset
from ... import dz,pyz
class Varset(Dataset):
    @staticmethod
    def fcs(fc, need_val = True):
        def _fc(kvs, ns=None, tag=None):
            if need_val:
                [fc(key, val, ns, tag) for key,val in kvs.items()]
            else:
                [fc(key, ns, tag) for key in kvs]
        return _fc
    def tag(self, _tag):
        if _tag is None:
            _tag = TagData.Key.Pub
        _tag = TagData.Key.stand(_tag)
        return _tag
    def init(self, ids):
        super().init(ids)
        self.vpops = self.fcs(self.vpop, 0)
        self.vremoves = self.fcs(self.vremove, 0)
        self.vsets = self.fcs(self.vset)
    def vpushs(self, kvs, ns=None,tag=None):
        [self.vpush(key, val, ns, tag) for key, val in kvs.items()]
        return pyz.with_out(lambda :self.vpops(kvs))
    def vset(self, key, val, ns=None, tag=None):
        tag = self.tag(tag)
        self.set(key, [val], ns, tag)
    def vget(self, key, ns=None, tag=None):
        tag = self.tag(tag)
        obj, find_tag, find = self.tget(key, ns, tag)
        if not find or len(obj)==0:
            return None, 0
        return obj[-1], 1
    def vhas(self, key, ns=None, tag=None):
        return self.vget(key, ns, tag)[1]
    def vpush(self, key, val, ns = None, tag = None):
        tag = self.tag(tag)
        obj, find_tag, find = self.tget(key, ns, tag)
        if not find or find_tag != tag:
            obj = []
        obj.append(val)
        self.set(key, obj, ns, tag)
    def vpop(self, key, ns=None, tag=None):
        tag = self.tag(tag)
        obj, find_tag, find = self.tget(key, ns, tag)
        if not find or find_tag != tag:
            return 0
        if len(obj)>0:
            obj.pop(-1)
        return 1
    def vremove(self, key, ns=None, tag=None):
        tag = self.tag(tag)
        obj, find_tag, find = self.tget(key, ns, tag)
        if not find or find_tag != tag:
            return 0
        if tag == TagData.Key.Pub:
            keys = self.ids(ns)+self.ids(key)
            dz.dremove(self.pub, keys)
        else:
            map = self.ns[ns]
            del map[key]
        return 1
        
