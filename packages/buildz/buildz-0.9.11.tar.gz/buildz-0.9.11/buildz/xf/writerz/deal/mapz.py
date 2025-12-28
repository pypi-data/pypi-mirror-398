
from .. import base
from .. import itemz
class MapDeal(base.BaseDeal):
    def height_tree(self, mg, maps):
        rst = []
        height = 1
        for key, val in maps.items():
            h_key = mg.height_tree(key)
            h_val = mg.height_tree(val)
            height = max(height, h_key[0]+1, h_val[0]+1)
            rst.append((h_key, h_val))
        return [height, rst]
    def init(self, left, right, st, spt):
        self.left = left
        self.right = right
        self.st = st
        self.spt = spt
    def deal(self, mg, maps, up_height, heights, conf, deep, top_not_format):
        aft_set = conf.s(" ")*conf.get(set=0)
        s_set = conf.s(self.st)+aft_set
        rst = []
        height = heights[0]
        for kv, _heights in zip(maps.items(), heights[1]):
            key, val = kv
            #for key, val in maps.items():
            skey = mg.deal(key, height, _heights[0], conf, deep+1)
            sval = mg.deal(val, height, _heights[1], conf, deep+1, top_not_format = 1)
            sitem = skey+s_set+sval
            rst.append(sitem)
        return self.deal_encape(rst, conf, deep, height,up_height, self.left, self.right, top_not_format)

pass 



            

                