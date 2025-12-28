from .. import base
from .. import item
from .. import exp
class LRDeal(base.BaseDeal):
    def check_right(self, obj):
        if obj.type!='str':
            return False
        val = obj.val
        if val.find(self.right)>=0:
            raise Exception(f"unexcept right symbol {self.right}")
        return True
    def labels(self):
        return [self.left]
    def types(self):
        return []
    def deal(self, buffer, rst, mg):
        cl = buffer.read(self.ll)
        if self.left!=cl:
            return False
        _arr = []
        rm = buffer.full().strip()
        buffer.clean2read(self.ll)
        if len(rm)>0:
            _arr.append(item.Item(rm, type="str", is_val=False))
        while True:
            cr = buffer.read(self.lr)
            if cr == self.right:
                rm = buffer.full().strip()
                buffer.clean2read(self.lr)
                break
            if not mg.deal(buffer, _arr):
                raise Exception("Error lr")
        buffer.clean()
        if len(rm)>0:
            _arr.append(item.Item(rm ,type = 'str', is_val=False))
        # dts = []
        # for k in _arr:
        #     _k = mg.build(k)
        #     if item.is_null(_k):
        #         continue
        #     dts.append(_k)
        #dts = [mg.build(k) for k in _arr]
        if self.mg_build:
            dts = mg.build_arr(_arr)
        else:
            dts = _arr
        obj = self.build_arr(dts)
        rst.append(obj)
        return True
    def to_vals(self, _arr, mg):
        dts = []
        for k in _arr:
            _k = mg.build(k)
            if item.is_null(_k):
                continue
            dts.append(_k)
        return dts
    def build_arr(self, obj):
        return item.Item(obj, type = self.type, is_val=True)
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def prepare(self, mg):
        self.left = mg.like(self.left)
        self.right = mg.like(self.right)
        self.ll = len(self.left)
        self.lr = len(self.right)
    def init(self, left, right, name= "lr", mg_build = True):
        self.left = left
        self.right = right
        self.ll = len(left)
        self.lr = len(right)
        self.name = name
        self.mg_build = mg_build
    def err(self, s):
        return s.replace("<lr>", self.name)

pass