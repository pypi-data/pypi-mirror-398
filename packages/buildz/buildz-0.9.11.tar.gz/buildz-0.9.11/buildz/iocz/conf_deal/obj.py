#

from .base import *
from ..ioc_deal import obj

class ObjectDeal(obj.ObjectDeal):
    def init(self):
        super().init()
        conf = BaseConf()
        conf.index(1, 'source', need=1)
        conf.index(2, 'args')
        conf.index(3, 'maps')
        conf.index(4, 'sets')
        conf.index(5, 'after_set')
        conf.key('source', 'src'.split(","), need=1)
        conf.key('before_set', 'before_call'.split(","))
        conf.key('after_set', 'after_call,call'.split(","))
        self.update = conf

pass