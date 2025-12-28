
from .. import base
from .. import itemz
import re
import json
class StrDeal(base.BaseDeal):
    def rpt(self, pt):
        st = self.like("^", pt)
        ed = self.like("$", pt)
        if pt[0]!=st:
            pt = st+pt
        if pt[-1]!=ed:
            pt = pt+ed
        return pt
    def init(self, left, right, pts = []):
        self.left = left
        self.right = right
        #self.single_line = single_line
        self.pts = [self.rpt(pt) for pt in pts]
    def deal(self, obj, conf):
        val = obj.val
        if type(val) not in [bytes, str]:
            return None
        et = self.like("\n", val)
        need_ep = 0
        if len(val)==0:
            need_ep = 1
        elif val.find(et)>=0:
            need_ep = 1
        else:
            for pt in self.pts:
                rpt = self.like(pt, val)
                if re.match(rpt, val) is not None:
                    need_ep = 1
                    break
        if need_ep:
            if type(val)==bytes:
                val = val.decode()
                val = json.dumps(val, ensure_ascii=False)[1:-1]
                val = val.encode()
            else:
                val = json.dumps(val, ensure_ascii=False)[1:-1]
            val = conf.s(self.left)+val+conf.s(self.right)
        return itemz.ShowItem(val, obj.deep, is_val=1, is_done=1)

pass 



            

                