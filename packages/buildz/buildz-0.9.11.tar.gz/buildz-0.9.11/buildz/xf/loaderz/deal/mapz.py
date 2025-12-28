from .. import base
from .. import item
from .. import exp
from . import lr
class MapDeal(lr.LRDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, left, right):
        super().init(left, right, "map")
    def types(self):
        return ['list']
    def build(self, obj):
        #if self.check_right(obj):
        #    return None
        val = obj.val
        if len(val)==0:
            obj.val = {}
            obj.is_val = 1
            return obj
        if len(val)%3!=0:
            return None
        opt = val[1]
        if opt.type!='kv':
            return None
        return self.build_arr(val, obj.pos)
    def build_arr(self, arr, arr_pos):
        rst = {}
        #pos = self.arr_pos(arr)#(arr[0].pos[0], arr[-1].pos[-1])
        if len(arr)%3!=0:
            raise exp.Exp(f"u f in map: {arr}", arr_pos)
        for i in range(0, len(arr), 3):
            k = arr[i]
            v = arr[i+2]
            opt = arr[i+1]
            if opt.type != "kv":
                raise exp.Exp(f"u f opt in map: {opt}", opt.pos)
            if type(k.val)==list:
                k.val = tuple(k.val)
            rst[k.val] = v.val
        return item.Item(rst, arr_pos, type='map', is_val = 1)

pass