from .. import base
from .. import item

class PrevSptDeal(base.BaseDeal):
    def labels(self):
        return [self.spt]
    def types(self):
        return [self.type]
    def build(self, obj):
        if self.ret is not None:
            obj.val = self.ret
            obj.is_val = 1
            return obj
        return item.null
    def prepare(self, mgs):
        self.spt = mgs.like(self.spt)
        self.l = len(self.spt)
    def deal(self, buffer, arr, mg):
        c = buffer.read(self.l)
        if c != self.spt:
            return False
        spt_pos = (buffer.read_base, buffer.read_base+self.l)
        rm = buffer.full().strip()
        rm_pos = buffer.pos()
        buffer.clean2read(self.l)
        it = item.Item(self.spt, spt_pos, type = self.type, is_val = 0)
        if len(rm)==0:
            if not self.allow_empty or (len(arr)>0 and arr[-1].is_val):    
                arr.append(it)
                return True
        obj = item.Item(rm, rm_pos, type = 'str', is_val = 0)
        arr.append(obj)
        arr.append(it)
        return True
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, spt, allow_empty = False, type = "spt", ret=None):
        self.spt = spt
        self.allow_empty = allow_empty
        self.l = len(spt)
        self.type = type
        self.ret = ret

pass