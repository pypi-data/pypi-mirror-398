
from .base import *
from ..ioc_deal import val
class ValDeal(val.ValDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'val', need=1)
        conf.key('val', 'value,data'.split(","), need=1)
        self.update = conf

pass