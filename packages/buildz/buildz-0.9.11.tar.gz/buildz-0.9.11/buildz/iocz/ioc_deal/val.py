
from .base import *
from ... import dz,pyz
from ..ioc.single import Single
class ValEncape(BaseEncape):
    '''
    '''
    def init(self, val):
        super().init()
        self.val = val
    def call(self, params=None, **maps):
        return self.val
class ValDeal(BaseDeal):
    def deal(self, conf, unit):
        assert 'val' in conf, f"[VAL] key 'val' not found in {conf}"
        return ValEncape(conf['val'])

pass