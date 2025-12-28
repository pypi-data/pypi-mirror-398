
from .base import *
from ... import dz,pyz
from ..ioc.single import Single
class RefEncape(BaseEncape):
    '''
    '''
    def init(self, ref, default, unit, env=-1):
        super().init()
        self.unit = unit
        self.ref, self.default = ref, default
        self.env = env
    def call(self, params=None, **maps):
        ref = self.ref
        if isinstance(ref, Encape):
            ref = ref(params)
        if self.env==0:
            obj, _, find = self.unit.get_env(ref)
            if find:
                return obj
        obj, find = self.unit.get(ref)
        if not find:
            if self.env==1:
                obj, _, find = self.unit.get_env(ref)
                if find:
                    return obj
            assert self.default[0], f"ref '{ref}' not found"
            val = self.default[1]
            if isinstance(val, Encape):
                val = val(params)
            obj = val
        return obj
class RefDeal(BaseDeal):
    def init(self, env = -1):
        super().init()
        self.env = env
    def deal(self, conf, unit):
        assert 'ref' in conf, f"[REF] key 'ref' not found in {conf}"
        ref = dz.g(conf, ref=None)
        if 'default' in conf:
            default = [1,conf['default']]
        else:
            default = [0,None]
        ref = self.get_encape(ref, unit)
        if default[0]:
            default[1] = self.get_encape(default[1], unit)
        env = None
        if 'env' in conf:
            env = conf['env']
        if env is None:
            env = self.env
        encape = RefEncape(ref, default, unit, env)
        return encape

pass