
from .base import *
from ... import dz,pyz
class MethodEncape(BaseEncape):
    def init(self, unit, method, obj, args, maps):
        super().init()
        self.unit = unit
        self.params = method, obj, args, maps
    def call(self, params=None, **_):
        method, obj, args, maps = self.params
        method = self.obj(method)
        if isinstance(obj, Encape):
            obj = self.obj(obj)
        elif type(obj)==str:
            obj, find = self.unit.get(obj)
        if obj is None and params is not None:
            obj = params.obj
        if type(method)==str:
            assert obj is not None and hasattr(obj, method)
            method = getattr(obj, method)
        args = self.elist2obj(args)
        maps = self.edict2obj(maps)
        return method(*args, **maps)
class MethodDeal(BaseDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.ikey(1, 'method','call,fc,data,key'.split(","), need=1)
        conf.ikey(2, 'obj', 'source,obj,object,src'.split(","))
        conf.ikey(3, 'args')
        conf.ikey(4, 'maps')
        self.update = conf
    def deal(self, conf, unit):
        assert 'method' in conf
        method = conf['method']
        method = self.get_encape(method, unit)
        obj = dz.get(conf, "obj")
        obj = self.get_encape(obj, unit)
        args = self.get_elist(unit, conf, 'args',[])
        maps = self.get_edict(unit, conf, 'maps', {})
        return MethodEncape(unit, method, obj, args, maps)

pass