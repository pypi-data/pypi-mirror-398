
from . import itemz
from ..readz import is_args
class Manager:
    def __init__(self):
        self.deals = {}
    def height_tree(self, obj):
        tobj = type(obj)
        if tobj not in self.deals:
            raise Exception(f"undealable type {tobj}=="+str(obj))
        for fc in self.deals[tobj]:
            rst = fc.height_tree(self, obj)
            if rst is not None:
                return rst
        raise Exception(f"undealable obj in type: {type(obj)}=="+str(obj))
    def add(self, types, fc):
        if type(types) not in (list, tuple):
            types = [types]
        for _type in types:
            if _type not in self.deals:
                self.deals[_type]=[]
            self.deals[_type].append(fc)
    def deal(self, obj, up_height, heights, conf, deep=1, top_not_format = 0):
        tobj = type(obj)
        if tobj not in self.deals:
            raise Exception("undealable type"+str(obj))
        for fc in self.deals[tobj]:
            rst = fc.deal(self, obj, up_height, heights, conf, deep, top_not_format)
            if rst is not None:
                return rst
        raise Exception("undealable obj in type"+str(obj))
    def dump(self, obj, conf):
        heights = self.height_tree(obj)
        rst = self.deal(obj, heights[0]+1, heights, conf)
        return rst

pass