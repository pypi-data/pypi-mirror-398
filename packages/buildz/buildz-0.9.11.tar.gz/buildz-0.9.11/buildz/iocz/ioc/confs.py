#
from .tdata import TagData
from .datas import Datas
from .dataset import Dataset
class Confs(Datas):
    @staticmethod
    def is_conf(obj):
        return type(obj) in (list, tuple, dict)
    def init(self, ns=None, id=None, deal_ns = None, dts=None):
        super().init(ns, id, dts)
        self.deal_ns = deal_ns
    def set(self, key, val, tag=None):
        val = (val, self.deal_ns, self.id)
        super().set(key, val, tag)
        
