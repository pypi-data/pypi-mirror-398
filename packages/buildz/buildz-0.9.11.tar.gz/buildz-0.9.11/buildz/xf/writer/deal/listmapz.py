
from .. import base
from .. import itemz
from ...readz import is_args
class ListMapDeal(base.BaseDeal):
    def init(self, left, right, st, spt):
        self.left = left
        self.right = right
        self.st = st
        self.spt = spt
    def deal(self, obj, conf):
        if not obj.check(is_args=1):
            return None
        list_num = obj.maps("list_num")
        arr = obj.val
        rs = None
        rst = []
        deep = 0
        for i in range(list_num):
            obj = arr[i]
            _val = obj.val
            deep = max(obj.deep+1, deep)
            if i < len(arr)-1:
                _val += conf.s(self.spt)
            rst.append(_val)
        aft_st = conf.s(" ")*conf.get(set=0)
        for i in range(list_num, len(arr), 2):
            obj_k = arr[i]
            obj_v = arr[i+1]
            _val = obj_k.val+conf.s(self.st)+aft_st+obj_v.val
            deep = max(obj_v.deep+1, deep)
            if i+1 < len(arr)-1:
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
        return itemz.ShowItem(rst, deep, is_args=1, is_done=1)

pass 



            

                