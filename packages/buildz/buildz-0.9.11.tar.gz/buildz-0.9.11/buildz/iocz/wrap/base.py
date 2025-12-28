
from ..ioc.base import *
from ... import dz, xf
def loads_xf(s):
    if type(s)!=str:
        return s
    return xf.loads(s)
class WrapItem(Base):
    def init(self, wrap, conf, add = False, remove=False):
        self.wrap = wrap
        self.add = add
        self.remove = remove
        self.conf = conf
    def call(self, cls):
        _id = id(cls)
        conf = self.wrap.update_wconf(_id, self.conf)
        if self.add:
            self.wrap.add_conf(conf)
            if self.remove:
                self.wrap.remove_wconf(_id)
        return cls
class WrapBase(Base):
    @staticmethod
    def loads(s):
        return loads_xf(s)
    @staticmethod
    def loads_list(arr):
        return [loads_xf(it) for it in arr]
    @staticmethod
    def loads_dict(maps):
        return {loads_xf(k):loads_xf(v) for k,v in maps.items()}
    def init(self, unit=None):
        self.wrap_conf = {}
        self.confs = []
        self.unit = None
        self.bind(unit)
    def clone(self, unit):
        return self.__class__(unit)
    def bind(self, unit):
        if self.unit == unit:
            return
        self.unit = unit
        for conf in self.confs:
            self.unit.add_conf(conf)
        self.confs = []
        return self
    def add_conf(self, conf):
        if self.unit is None:
            self.confs.append(conf)
        else:
            self.unit.add_conf(conf)
    def update_wconf(self, id, conf):
        if id not in self.wrap_conf:
            self.wrap_conf[id] = {}
        curr = self.wrap_conf[id]
        dz.fill(conf, curr)
        return curr
    def remove_wconf(self, id):
        if id in self.wrap_conf:
            del self.wrap_conf[id]
