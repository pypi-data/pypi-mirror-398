from .. import base
from .. import item
from .. import exp
from . import spt
class SetDeal(spt.PrevSptDeal):
    """
        Map里的key-val读取
    """
    
    def init(self, spt):
        super().init(spt, True,"kv")
    def build(self, obj):
        return obj

pass