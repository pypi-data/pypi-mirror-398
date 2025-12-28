
from .base import *
from ... import dz,pyz
class CallEncape(BaseEncape):
    def init(self, unit, call, args, maps):
        super().init()
        self.unit = unit
        self.params = call, args, maps
    def call(self, params=None, **_):
        call, args, maps = self.params
        call = self.obj(call)
        if type(call)==str:
            call,find = self.unit.get(call)
        assert call is not None
        args = self.elist2obj(args)
        maps = self.edict2obj(maps)
        return call(*args, **maps)
class CallDeal(BaseDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'call', need=1)
        conf.index(2, 'args')
        conf.index(3, 'maps')
        conf.key('call', need=1)
        self.update = conf
    def deal(self, conf, unit):
        assert 'call' in conf
        call = conf['call']
        call = self.get_encape(call, unit)
        args = self.get_elist(unit, conf, 'args',[])
        maps = self.get_edict(unit, conf, 'maps', {})
        return CallEncape(unit, call, args, maps)

pass