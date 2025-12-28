from ..base import *
basepath = path
path = pathz.Path()
path.set("conf", basepath.local("ioc/conf"), curr=0)
class Encape(Base):
    def call(self, params=None, **maps):
        return None

pass
class Deal(Base):
    def deal(self, conf, unit):
        return None
    def update(self, conf, unit):
        return conf, False
    def call(self, conf, unit):
        'encape, conf, conf_need_udpate'
        conf, upd = self.update(conf, unit)
        encape = self.deal(conf,unit)
        return encape,conf,upd

pass

class Params(Base):
    def str(self):
        return f"iocz.Params(args={self.args}, maps={self.maps})"
    @staticmethod
    def Clone(params, **upds):
        if params is None:
            args,maps = [],{}
        else:
            args, maps = list(params.args), dict(params.maps)
        maps.update(upds)
        obj = Params()
        obj.args = args
        obj.maps = maps
        return obj
    def clone(self, **upds):
        return Params.Clone(self, **upds)
    def init(self, *args, **maps):
        self.args = args
        self.maps = maps
    def set(self, key, val):
        self.maps[key] = val
    def get(self, key, default=None):
        if key not in self.maps:
            return default
        return self.maps[key]
    def __getattr__(self, key):
        if key not in self.maps:
            return None
        return self.maps[key]

pass