
from .. import base
from .. import itemz
import re
import json
class ValDeal(base.BaseDeal):
    def deal(self, obj, conf):
        if not obj.check(is_val=1):
            return None
        val = obj.val
        if type(val) in [list, dict, tuple]:
            return None
        val = conf.s(json.dumps(val, ensure_ascii=False))
        return itemz.ShowItem(val, obj.deep, is_val=1, is_done=1)

pass 



            

                