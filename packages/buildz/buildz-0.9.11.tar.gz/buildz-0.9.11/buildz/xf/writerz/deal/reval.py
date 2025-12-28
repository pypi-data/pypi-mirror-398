
from .. import base
from .. import itemz
import re
import json
class ValDeal(base.BaseDeal):
    def init(self, fc):
        self.fc = fc
    def deal(self, mg, obj, up_height, heights, conf, deep, top_not_format):
        val = conf.s(self.fc(obj))
        val = self.prev_spc(conf, deep, up_height, top_not_format)+val
        return val

pass 



            

                