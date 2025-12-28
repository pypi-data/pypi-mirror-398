
from . import buffer
from . import base
from . import pos
from . import exp
from . import item
from ..stack import Stack
class Manager:
    def __init__(self, as_bytes = False):
        self.index = 0
        self.as_bytes = as_bytes
        if as_bytes:
            self.type = bytes
        else:
            self.type = str
        self.deals = {}
        self.builds = {}
        self.default_deal = self.like("")
    def default_deals(self):
        return self.deals[self.default_deal]
    def get_deals(self, c):
        if c in self.deals:
            return self.deals[c]
        return []
    def like(self, s):
        if self.type ==type(s):
            return s
        if type(s)==str:
            return s.encode()
        return s.decode()
    def add(self,obj):
        obj.regist(self)
        lbs = obj.labels()
        lbs = [self.like(k[:1]) for k in lbs]
        for lb in lbs:
            if lb not in self.deals:
                self.deals[lb] = []
            self.deals[lb].append(obj)
        types = obj.types()
        for _type in types:
            if _type not in self.builds:
                self.builds[_type] = []
            self.builds[_type].append(obj)
        return self
    def do(self, fcs, *argv, **maps):
        for fc in fcs:
            if fc(*argv, **maps):
                return True
        return False
    def regist(self):
        id = self.index
        self.index+=1
        return "id_"+str(id)
    def build(self, obj):
        if obj.is_val:
            return obj
        #print(f"[TESTZ] obj: {obj}")
        _type = obj.type
        if _type not in self.builds:
            raise exp.Exp(f"unspt type: {_type}", obj.pos)
        builds = self.builds[_type]
        for deal in builds:
            rst = deal.build(obj)
            if rst is not None:
                return rst
        raise exp.Exp(f"unspt deal type:[{obj}]", obj.pos)
    def deal(self, buffer, arr):
        c = buffer.read()
        if len(c)==0 and buffer.size()==0:
            return False
        deals = self.get_deals(c)
        find = False
        for deal in deals:
            if deal.deal(buffer, arr, self):
                return True
        deals = self.default_deals()
        for deal in deals:
            if deal.deal(buffer, arr, self):
                return True
        return False
    def build_arr(self, _arr):
        dts = []
        for k in _arr:
            _k = self.build(k)
            if item.is_null(_k):
                continue
            dts.append(_k)
        return dts
    def load(self, buffer):
        try:
            return self._load(buffer)
        except exp.Exp as _exp:
            #import traceback
            #traceback.print_exc()
            exp.deal(_exp, buffer)
    def _load(self, buffer):
        arr = []
        while self.deal(buffer, arr):
            pass
        arr = self.build_arr(arr)
        arr_pos = base.arr_pos(arr)#(arr[0].pos[0], arr[-1].pos[-1])
        #print(f"mg arr: {arr}")
        obj = item.Item(arr, arr_pos, type = "list", is_val = 0)
        obj = self.build(obj)
        #arr = rst
        #if len(arr)==1:
        #    arr = arr[0]
        val = obj.val
        #print(f"mg val:{val}")
        if type(val) in [list,map] and len(val)==0:
            val = ""
        if type(val)==list and len(val)==1:
            val = val[0]
        return val
    def loads(self, reader):
        if type(reader) == self.type:
            #print(f"try str, {len(reader)}")
            buff = buffer.StrBuffer(reader)
        else:
            buff = buffer.Buffer(reader)
        return self.load(buff)

pass
