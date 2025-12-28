from ..ioc.base import *
from ..ioc.confs import Confs
from ... import dz,pyz
class CacheLoads(Base):
    def init(self):
        self.loads = {}
    def call(self, src):
        if src not in self.loads:
            self.loads[src] = pyz.load(src)
        return self.loads[src]

pass
loads = CacheLoads()
class BaseEncape(Encape):
    load = loads
    def elist2obj(self, list, params=None):
        return [self.obj(k,params) for k in list]
    def edict2obj(self, list, params=None, dict=True):
        if dict:
            return {self.obj(k, params):self.obj(v, params) for k,v in list}
        else:
            return [[self.obj(it, params) for it in k] for k in list]
    @staticmethod
    def obj(val,*a,**b):
        if not isinstance(val, Encape):
            return val
        return val(*a,**b)

pass
class BaseDeal(Deal):
    load = loads
    def get_elist(self, unit, conf, key, default=[]):
        val = None
        if key in conf:
            val = conf[key]
        if val is None:
            val = default
        return self.list2encape(val, unit)
    def get_edict(self, unit, conf, key, default={}):
        val = None
        if key in conf:
            val = conf[key]
        if val is None:
            val = default
        return self.dict2encape(val, unit)
    def dict2encape(self, maps, unit):
        rst = []
        for k,v in dz.dict2iter(maps):
            rst.append((self.get_encape(k, unit),self.get_encape(v, unit)))
        return rst
    def list2encape(self, list, unit):
        list = [self.get_encape(k, unit) for k in list]
        return list
    def init(self):
        self.cache_encapes = {}
    def cache_get(self, key, ns):
        if key is None:
            return None
        key = (ns, key)
        return dz.get(self.cache_encapes, key, None)
    def cache_set(self, key, ns, encape):
        if key is None:
            return
        key = (ns, key)
        self.cache_encapes[key] = encape
    @staticmethod
    def get_encape(key, unit):
        if Confs.is_conf(key):
            ep,_,find = unit.get_encape(key, unit)
            assert find
            return ep
        return key
    def call(self, conf, unit):
        'encape, conf, conf_need_udpate'
        id,find=unit.conf_key(conf)
        ns = unit.ns
        encape = self.cache_get(id, ns)
        if encape is not None:
            return encape, conf, False
        conf, upd = self.update(conf, unit)
        encape = self.deal(conf,unit)
        self.cache_set(id, ns, encape)
        return encape,conf,upd

pass
