
from .base import *
from ... import dz,pyz
from .val import ValEncape
class IOCDeal(BaseDeal):
    def deal(self, conf, unit):
        target = dz.g(conf, target='unit')
        data = None
        if target == 'unit':
            data = unit
        elif target =='conf':
            data = conf
        elif target in ('manager','mg'):
            data = unit.mg
        assert data is not None, f"[IOC] unknown target '{target}' in {conf}"
        return ValEncape(data)

pass