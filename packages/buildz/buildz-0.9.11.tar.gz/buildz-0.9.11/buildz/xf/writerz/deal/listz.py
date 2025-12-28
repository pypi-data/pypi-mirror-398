
from .. import base
from .. import itemz
class ListDeal(base.BaseDeal):
    def height_tree(self, mg, arr):
        rst = []
        height = 1
        for obj in arr:
            _h = mg.height_tree(obj)
            height = max(height, _h[0]+1)
            rst.append(_h)
        return [height, rst]
    def init(self, left, right, spt):
        self.left = left
        self.right = right
        self.spt = spt
    def deal(self, mg, arr, up_height, heights, conf, deep, top_not_format):
        rst = []
        height = heights[0]
        for obj, _heights in zip(arr, heights[1]):
            sitem = mg.deal(obj, height, _heights, conf, deep+1)
            rst.append(sitem)
        return self.deal_encape(rst, conf, deep, height,up_height, self.left, self.right, top_not_format)

pass 



            

                