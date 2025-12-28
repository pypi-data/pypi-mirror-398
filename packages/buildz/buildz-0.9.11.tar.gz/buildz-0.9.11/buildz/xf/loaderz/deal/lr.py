from .. import base
from .. import item
from .. import exp
class LRDeal(base.BaseDeal):
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
        rm_pos = buffer.pos()
        buffer.clean2read(self.ll)
        if len(rm)>0:
            _arr.append(item.Item(rm, rm_pos, type="str", is_val=False))
        arr_pos = list(rm_pos)
        while True:
            cr = buffer.read(self.lr)
            if cr == self.right:
                rm = buffer.full().strip()
                rm_pos = buffer.pos()
                buffer.clean2read(self.lr)
                break
            if not mg.deal(buffer, _arr):
                e_pos = buffer.pos()
                raise exp.Exp("Error lr", e_pos)
        buffer.clean()
        arr_pos[1] = rm_pos[1]
        arr_pos = tuple(arr_pos)
        if len(rm)>0:
            _arr.append(item.Item(rm , rm_pos, type = 'str', is_val=False))
        if self.mg_build:
            dts = mg.build_arr(_arr)
        else:
            dts = _arr
        obj = self.build_arr(dts, arr_pos)
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
    def build_arr(self, obj, arr_pos):
        return item.Item(obj, arr_pos, type = self.type, is_val=True)
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