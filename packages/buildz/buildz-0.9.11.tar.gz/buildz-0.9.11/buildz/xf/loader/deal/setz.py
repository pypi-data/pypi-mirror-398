from .. import base
from .. import item
from .. import exp
from . import spt
class SetDeal(spt.PrevSptDeal):
    """
        Map里的key-val读取
    """
    def init(self, spt):
        self.sp().init(spt, True)
    def deal(self, queue, stack):
        if len(stack)<3:
            return False
        if not stack[-1].check(is_val=1):
            return False
        if not stack[-3].check(is_val=1):
            return False
        if not stack[-2].check(type=self.id()):
            return False
        if stack[-2].check(is_keyval=1):
            return False
        val = stack.pop(-1)
        spt = stack.pop(-1)
        key = stack.pop(-1)
        if not key.check(is_val=1):
            print("key:", key)
            raise exp.FormatExp("not an usable key in key-val paris", key.pos, key.val)
        if not val.check(is_val=1):
            print("vak:", val)
            raise exp.FormatExp("not an usable val in key-val paris", val.pos, val.val)
        rst = [key.val, val.val]
        stack.append(item.DealItem(rst, key.pos, self.id(), is_keyval = 1))
        return True

pass