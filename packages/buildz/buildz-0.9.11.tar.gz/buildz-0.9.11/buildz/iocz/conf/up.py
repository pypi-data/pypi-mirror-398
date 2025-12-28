#
from .conf import Conf
from .base import Base
from ... import dz
class Up(Conf):
    def init(self):
        super().init()
        self.key('up', 'parent,parents'.split(","))
    def call(self, conf, unit):
        conf, upd = super().call(conf, unit)
        if 'up' in conf:
            up = conf['up']
            up_conf, tag, find = unit.get_conf(up)
            assert find, f"up '{up}' not found in {conf}"
            assert dz.isdict(up_conf), f"up '{up}' should be dict, but list found: {up_conf}"
            dz.fill(up_conf, conf, 0)
            upd = 1
        return conf, upd

pass

class BaseConf(Up):
    def init(self):
        super().init()
        conf = Conf()
        conf.index(0, 'type', need=1)
        conf.index(1, 'id', need=0)
        conf.index(2, 'single', need=0)
        self.index(0, deal=conf, need=1, dict_out=1)