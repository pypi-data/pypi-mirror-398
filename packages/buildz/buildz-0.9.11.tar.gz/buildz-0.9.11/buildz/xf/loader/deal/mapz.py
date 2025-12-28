from .. import base
from .. import item
from .. import exp
from . import lr
class MapDeal(lr.LRDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, left, right):
        self.sp().init(left, right, "map")
    def build(self, arr, l_item):
        rst = []
        for _item in arr:
            if not _item.check(is_keyval = 1):
                print(arr)
                print("error _item:", _item)
                raise exp.FormatExp("an not key-val item find in map", _item.pos, _item.val)
            rst.append(_item.val)
        maps = {k[0]:k[1] for k in rst}
        return item.DealItem(maps, l_item.pos, self.id(), is_val = 1, is_map = 1)

pass