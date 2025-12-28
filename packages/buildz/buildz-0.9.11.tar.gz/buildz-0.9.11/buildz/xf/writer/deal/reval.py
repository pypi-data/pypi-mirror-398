
from .. import base
from .. import itemz
import re
import json
class ValDeal(base.BaseDeal):
    def init(self, tp, fc):
        self._type  = tp
        self.fc = fc
    def deal(self, obj, conf):
        if not obj.check(is_val=1):
            return None
        val = obj.val
        if type(val)!=self._type:
            return None
        val = conf.s(self.fc(val))
        return itemz.ShowItem(val, obj.deep, is_val=1, is_done=1)

pass 



            

                