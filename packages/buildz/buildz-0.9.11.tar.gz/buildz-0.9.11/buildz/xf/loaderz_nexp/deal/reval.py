from .. import base
from .. import item
from .. import exp
from . import lr
import re
class ValDeal(base.BaseDeal):
    def prepare(self,mg):
        self.pt = mg.like(self.pt)
        self.type = mg.type
    def types(self):
        return ["str"]
    """
        正则表达式匹配
    """
    def init(self, pt, fc):
        st = "^"
        ed = "$"
        if pt[0]!=st:
            pt = st+pt
        if pt[-1]!=ed:
            pt = pt+ed
        self.pt = pt
        self.fc = fc
    def build(self, obj):
        val = obj.val
        if type(val) != self.type:
            return None
        if re.match(self.pt, val) is None:
            return None
        val = self.fc(val)
        return item.Item(val, type = "val", is_val = 1)

pass