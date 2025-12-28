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
        super().init(left, right, 'lrval', False)
        self.fc = fc
    def build_arr(self, arr, arr_pos):
        rst = []
        #pos = self.arr_pos(arr)#(arr[0].pos[0], arr[-1].pos[-1])
        if len(arr)!=3:
            raise exp.Exp(f"error in lrval:{arr}", arr_pos)
        for _item in arr[::2]:
            if type(_item.val)!=str:
                raise exp.Exp(f"error in list:{_item}", _item.pos)
            rst.append(_item.val)
        try:
            val = self.fc(rst[0], rst[1])
        except Exception as exp1:
            print("exp:", exp1)
            raise exp.Exp(f"error in lrval fc: {self.fc}({rst}): {exp1} ", pos)
        return item.Item(val, arr_pos, type='val', is_val = 1)
    def build_arrx(self, arr, arr_pos):
        return self.build(obj)

pass
