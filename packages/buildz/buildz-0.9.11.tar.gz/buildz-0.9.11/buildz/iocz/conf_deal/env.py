
from .base import *
from ... import dz,pyz
class EnvEncape(BaseEncape):
    def init(self, unit, env, default):
        super().init()
        self.unit = unit
        self.params = env, default
    def call(self, params=None, **_):
        env, default = self.params
        env = self.obj(env)
        obj, _, find = self.unit.get_env(env)
        if find:
            return obj
        assert default[0], f"env '{env}' not found"
        obj = default[1]
        obj = self.obj(obj)
        return obj
class EnvDeal(BaseDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'env', need=1)
        conf.index(2, 'default')
        conf.key('env', "data,key,profile,conf".split(","), need=1)
        self.update = conf
    def deal(self, conf, unit):
        assert 'env' in conf
        env = self.get_encape(conf['env'], unit)
        default, dfind = dz.dget(conf, 'default')
        if dfind:
            default = self.get_encape(default, unit)
        return EnvEncape(unit, env, [dfind, default])

pass