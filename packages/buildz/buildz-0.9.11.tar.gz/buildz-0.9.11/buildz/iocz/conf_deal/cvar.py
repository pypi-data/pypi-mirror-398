
from .base import *
from ... import dz,pyz
class CVarEncape(BaseEncape):
    def init(self, cvar):
        super().init()
        self.cvar = cvar
    def call(self, params=None, **maps):
        cvar = self.cvar
        if isinstance(cvar, Encape):
            cvar = cvar()
        cvar = self.load(cvar)
        return cvar
class CVarDeal(BaseDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'cvar', need=1)
        conf.key('cvar', 'var,data'.split(","), need=1)
        self.update = conf
    def deal(self, conf, unit):
        assert 'cvar' in conf
        cvar = conf['cvar']
        if Confs.is_conf(cvar):
            cvar = self.get_encape(cvar, unit)
        return CVarEncape(cvar)

pass