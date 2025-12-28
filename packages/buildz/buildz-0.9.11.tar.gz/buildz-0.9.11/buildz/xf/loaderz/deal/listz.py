from .. import base
from .. import item
from .. import exp
from . import lr
class ListDeal(lr.LRDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, left, right):
        super().init(left, right, 'list')
    def types(self):
        return ['list']
    def build(self, obj):
        val = obj.val
        if len(val)==0:
            obj.val = []
            obj.is_val = 1
            return obj
        if len(val)>1:
            opt = val[1]
            if opt.type=='kv':
                return None
        return self.build_arr(val, obj.pos)
    def build_arr(self, arr, arr_pos):
        rst = []
        #pos = self.arr_pos(arr)#(arr[0].pos[0],arr[-1].pos[-1])
        for _item in arr:
            if not _item.is_val:
                raise exp.Exp(f"error in list: item is not val: {_item}", _item.pos)
            rst.append(_item.val)
        return item.Item(rst, arr_pos, type='list', is_val = 1)

pass