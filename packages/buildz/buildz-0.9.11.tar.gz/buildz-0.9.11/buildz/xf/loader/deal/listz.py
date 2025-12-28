from .. import base
from .. import item
from .. import exp
from . import lr
class ListDeal(lr.LRDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, left, right):
        self.sp().init(left, right, 'list')
    def build(self, arr, l_item):
        rst = []
        for _item in arr:
            if not _item.check(is_val = 1):
                raise exp.FormatExp("format error find in list:", _item.pos, _item.val)
            rst.append(_item.val)
        return item.DealItem(rst, l_item.pos, self.id(), is_val = 1, is_list = 1)

pass