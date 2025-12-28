

from ..base import Base
from . import mapz
class Mapz(Base):
    def init(self, spt = ".", code='utf-8'):
        self.spt = spt
        self.map = {}
        self.code = code
    def keys(self, key):
        if type(key) not in (list, tuple):
            if type(key)==bytes:
                key = key.decode(self.code)
            if type(key)!=str:
                key = str(key)
            key = key.split(self.spt)
        return key
    def get(self, keys):
        keys = self.keys(keys)
        val, find = mapz.dget(self.map, keys, default=None)
        if not find:
            raise KeyError(str(keys))
        return val
    def set(self, keys, val):
        keys = self.keys(keys)
        mapz.dset(self.map, keys, val)
    def has(self, keys):
        keys = self.keys(keys)
        return mapz.dhas(self.map, keys)
    def remove(self, keys):
        keys = self.keys(keys)
        if not self.has(keys):
            raise KeyError(keys)
        mapz.dremove(self.map, keys)
    def __getitem__(self, keys):
        return self.get(keys)
    def __setitem__(self, keys, val):
        self.set(keys, val)
    def __contains__(self, keys):
        return self.has(keys)
    def __delitem__(self, keys):
        return self.remove(keys)