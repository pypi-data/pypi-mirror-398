
from .. import base
from .. import itemz
from ...readz import is_args
class ListMapDeal(base.BaseDeal):
    def height_tree(self, mg, obj):
        arr = obj.args
        maps = obj.maps
        rst = []
        height = 1
        rst_arr = []
        for obj in arr:
            _h = mg.height_tree(obj)
            height = max(height, _h[0]+1)
            rst_arr.append(_h)
        rst_maps = []
        for key, val in maps.items():
            h_key = mg.height_tree(key)
            h_val = mg.height_tree(val)
            height = max(height, h_key[0]+1, h_val[0]+1)
            rst_maps.append((h_key, h_val))
        return [height, rst_arr, rst_maps]
    def init(self, left, right, st, spt):
        self.left = left
        self.right = right
        self.st = st
        self.spt = spt
    def deal(self, mg, obj, up_height, heights, conf, deep, top_not_format):
        height = 1
        aft_set = conf.s(" ")*conf.get(set=0)
        s_set = conf.s(self.st)+aft_set
        arr = obj.args
        maps = obj.maps
        rst = []
        height = heights[0]
        for obj, _heights in zip(arr, heights[1]):
            sitem = mg.deal(obj, height, _heights, conf, deep+1)
            rst.append(sitem)
        for kv, _heights in zip(maps.items(), heights[2]):
            key, val = kv
            skey = mg.deal(key, height, _heights[0], conf, deep+1)
            sval = mg.deal(val, height, _heights[1], conf, deep+1, top_not_format = 1)
            sitem = skey+s_set+sval
            rst.append(sitem)
        return self.deal_encape(rst, conf, deep, height,up_height, self.left, self.right, top_not_format)

pass 



            

                