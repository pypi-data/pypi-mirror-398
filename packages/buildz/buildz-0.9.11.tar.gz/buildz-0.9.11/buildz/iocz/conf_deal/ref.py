
from .base import *
from ..ioc_deal import ref
class RefDeal(ref.RefDeal):
    def init(self, env=-1):
        super().init(env)
        conf = BaseConf()
        conf.ikey(1, 'ref', 'key,data'.split(","), need=1)
        conf.index(2, 'default')
        conf.ikey(3, 'env', 'profile'.split(','))
        self.update = conf

pass
