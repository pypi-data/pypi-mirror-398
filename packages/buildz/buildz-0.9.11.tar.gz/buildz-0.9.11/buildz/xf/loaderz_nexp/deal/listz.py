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
        #print(f"list build: {obj}")
        #if self.check_right(obj):
        #    return None
        val = obj.val
        if len(val)==0:
            obj.val = []
            obj.is_val = 1
            return obj
        if len(val)>1:
            opt = val[1]
            if opt.type=='kv':
                return None
        return self.build_arr(val)
    def build_arr(self, arr):
        rst = []
        for _item in arr:
            if not _item.is_val:
                raise Exception(f"error in list:{_item}")
            rst.append(_item.val)
        return item.Item(rst, type='list', is_val = 1)

pass