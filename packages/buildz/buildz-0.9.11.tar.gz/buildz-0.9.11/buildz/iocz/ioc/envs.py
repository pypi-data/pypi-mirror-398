#
from .datas import Datas
from .dataset import Dataset
from .confs import Confs
class Envs(Datas):
    def init(self, ns=None, id=None, dts=None):
        super().init(ns, id, dts)
        self.ids = None
        self.caches = {}
    def update(self, maps, tag=None, flush=False):
        if flush:
            maps = dz.unflush_maps(maps, self.ids.id)
        for key, val in maps.items():
            self.set(key, val, tag)
    def bind(self, dts):
        self.ids = dts.ids
        super().bind(dts)
        for k,v in self.caches.items():
            val,tag=v
            self.set(k,val,tag)
        self.caches = {}
    def set(self, key, val, tag=None):
        if self.ids is not None:
            super().set(self.ids(key), val, tag)
        else:
            self.caches[key] = val,tag
    def get(self, key, tags=None):
        return super().get(self.ids(key), tags)