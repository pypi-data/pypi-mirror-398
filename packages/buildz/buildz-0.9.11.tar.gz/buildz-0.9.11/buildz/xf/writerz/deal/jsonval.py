
from .. import base
from .. import itemz
import re
import json
class ValDeal(base.BaseDeal):
    def deal(self, mg, val, up_height, heights, conf, deep, top_not_format):
        val = conf.s(json.dumps(val, ensure_ascii=False))
        return self.prev_spc(conf, deep, up_height, top_not_format)+val
pass 



            

                