from .. import base
from .. import item
from .. import exp
from . import lr
from . import reval
class Fcs:
    def __init__(self):
        self.maps = {}
    def set(self, _type, fc):
        self.maps[_type] = fc
    def __call__(self, val, _type):
        if _type not in self.maps:
            raise Exception("unreginize type:"+_type)
        return self.maps[_type](val)

pass


class LRValDeal(lr.LRDeal):
    """
    """
    def init(self, left, right, fc):
        self.sp().init(left, right, 'lrval')
        self.fc = fc
    def build(self, arr, l_item):
        rst = []
        if len(arr)!=2:
            raise exp.FormatExp("format error find in lrval:", l_item.pos, l_item.val)
        for _item in arr:
            if not _item.check(is_val = 1):
                raise exp.FormatExp("format error find in list:", _item.pos, _item.val)
            rst.append(_item.val)
        try:
            val = self.fc(rst[0], rst[1])
        except Exception as exp1:
            print("exp:", exp1)
            raise exp.FormatExp("error in lrval fc:\""+str(exp1)+"\"", arr[0].pos, arr[0].val)
        return item.DealItem(val, l_item.pos, self.id(), is_val = 1, is_lrval = 1)

pass

class LRReValDeal(reval.ValDeal):
    """
    """
    def efc(self, val):
        arr = val.split(self.like(self.spt, val))
        val, _type = arr
        return self._fc(val, _type)
    def init(self, spt, fc):
        self.spt = spt
        self._fc = fc
        pt = "^.+\s*\\"+spt+"\s*.+$"
        self.sp().init(pt, self.efc)

pass