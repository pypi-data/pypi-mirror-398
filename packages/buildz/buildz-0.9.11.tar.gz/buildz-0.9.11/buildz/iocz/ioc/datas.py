
from ... import pyz, dz
from .tdata import TagData
class Datas(TagData):
    '''
        一个单元下的数据集
    '''
    def init(self, ns=None, id=None, dts=None):
        super().init(ns, id)
        self.dts = dts
    def bind(self, dts):
        if self.dts==dts:
            return
        self.dts = dts
        dts.add(self)
    def update(self, maps, tag=None):
        for key, val in maps.items():
            self.set(key, val, tag)
    def set(self, key, val, tag=None):
        tag = pyz.nnull(tag, self.default)
        tag = TagData.Key.stand(tag)
        super().set(key, val, tag)
        if self.dts is not None and tag in (TagData.Key.Pub, TagData.Key.Ns):
                self.dts.set(key, val, self.ns, tag, self)
    def tget(self, key, src=None,id=None, gfind=True):
        ns, id = self.nsid(src, id)
        obj, tag, find=super().tget(key, ns, id)
        if not find and gfind:
            obj, tag, find = self.dts.tget(key, ns, id)
        return obj, tag, find
