
from .base import *
from ..ioc_deal import ioc
class IOCDeal(ioc.IOCDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'target')
        conf.key('target', 'data,key'.split(","))
        self.update = conf

pass