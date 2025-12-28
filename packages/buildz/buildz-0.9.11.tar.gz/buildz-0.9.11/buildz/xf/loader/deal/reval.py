from .. import base
from .. import item
from .. import exp
from . import lr
import re
class ValDeal(base.BaseDeal):
    def has_prev(self):
        return 0
    def has_deal(self):
        return 1
    """
        正则表达式匹配
    """
    def init(self, pt, fc):
        st = self.like("^", pt)
        ed = self.like("$", pt)
        if pt[0]!=st:
            pt = st+pt
        if pt[-1]!=ed:
            pt = pt+ed
        self.pt = pt
        self.fc = fc
    def deal(self, queue, stack):
        if len(queue)==0:
            return False
        _item = queue[0]
        if not _item.check(is_val=1, type = None):
            return False
        val = _item.val
        if type(val) not in [bytes, str]:
            return False
        pt = self.like(self.pt, val)
        if re.match(pt, val) is None:
            return False
        try:
            val = self.fc(val)
        except Exception as exp1:
            print("exp:", exp1)
            raise exp.FormatExp("error in reval fc:\""+str(exp1)+"\"", _item.pos, _item.val)
        queue.pop(0)
        out_item = item.DealItem(val, _item.pos, self.id(), is_val = 1)
        stack.append(out_item)
        return True

pass