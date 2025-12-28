
from .base import *
from ..ioc_deal import deal
class DealDeal(deal.DealDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.ikey(1, 'source', 'src'.split(","), need=1)
        conf.index(2, 'call')
        conf.ikey(3, 'deals', 'deal'.split(","))
        conf.index(4, 'tag')
        self.update = conf

pass