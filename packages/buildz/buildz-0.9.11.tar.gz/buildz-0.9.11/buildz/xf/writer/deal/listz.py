
from .. import base
from .. import itemz
class ListDeal(base.BaseDeal):
    def init(self, left, right, spt):
        self.left = left
        self.right = right
        self.spt = spt
    def deal(self, obj, conf):
        if not obj.check(is_list=1):
            return None
        arr = obj.val
        rs = None
        rst = []
        deep = 0
        for i in range(len(arr)):
            obj = arr[i]
            _val = obj.val
            deep = max(obj.deep+1, deep)
            if i < len(arr)-1:
                _val += conf.s(self.spt)
            rst.append(_val)
        if not conf.check(format=1) or conf.get(deep=0)+1>=deep:
            spc = conf.s(" ")*conf.get(prev=0)
            rst = spc.join(rst)
        else:
            rst = [self.fmt(k, conf.get(line=4), conf.get(spc=' ')) for k in rst]
            rst = conf.s("\n").join(rst)
            rst = conf.s("\n")+rst+conf.s("\n")
        rst = conf.s(self.left)+rst+conf.s(self.right)
        return itemz.ShowItem(rst, deep, is_list=1, is_done=1)

pass 



            

                