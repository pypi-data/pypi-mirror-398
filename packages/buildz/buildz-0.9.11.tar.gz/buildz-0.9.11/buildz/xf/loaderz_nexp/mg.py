
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
            raise Exception("unspt type:"+_type)
        builds = self.builds[_type]
        for deal in builds:
            rst = deal.build(obj)
            if rst is not None:
                return rst
        raise Exception(f"unspt deal type:[{obj}]")
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
        arr = []
        while self.deal(buffer, arr):
            pass
        #arr = [k.val for k in arr]
        #rst = []
        # for k in arr:
        #     if type(k) == self.type:
        #         if len(k.strip())==0:
        #             continue
        #     rst.append(k)
        #print(f"mg arr: {arr}")
        arr = self.build_arr(arr)
        #print(f"mg arr: {arr}")
        obj = item.Item(arr, type = "list", is_val = 0)
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
