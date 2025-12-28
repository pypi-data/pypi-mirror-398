
from .base import *
from ... import dz,pyz,xf
class AttrEncape(BaseEncape):
    def init(self, unit, attr, obj):
        super().init()
        self.unit = unit
        self.params = attr, obj
    def call(self, params=None, **maps):
        attr, obj = self.params
        attr = self.obj(attr)
        if isinstance(obj, Encape):
            obj = self.obj(obj)
        elif type(obj)==str:
            obj, find = self.unit.get(obj)
        if obj is None and params is not None:
            obj = params.obj
        assert obj is not None and hasattr(obj, attr), f"attr get failed for "
        return getattr(obj, attr)
class AttrDeal(BaseDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.ikey(1, 'attr', 'var,data,key'.split(","), need=1)
        conf.ikey(2, 'obj', 'object,src,source'.split(','))
        self.update = conf
    def deal(self, conf, unit):
        assert 'attr' in conf
        attr = conf['attr']
        attr = self.get_encape(attr, unit)
        # obj = dz.g(conf, obj=None)
        # print(f"obj: {obj}")
        # exit()
        obj = dz.get(conf, 'obj')
        obj = self.get_encape(obj, unit)
        return AttrEncape(unit, attr, obj)

pass