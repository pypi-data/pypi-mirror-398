
from . import buffer
from . import base
from . import pos
from . import exp
from ..stack import Stack
class Manager:
    def fcs(self, fc, *args, **maps):
        return fc(*self.cs(*args), **maps)
    def add_fc(self, fc, *args, **maps):
        obj = self.fcs(fc, *args, **maps)
        self.add(obj)
        return self
    def cs(self, *args):
        return [self.c(k) for k in args]
    def c(self, s):
        if self.bts:
            s = s.encode(self.code)
        return s
    # 上面这些没用
    def add(self,obj):
        #obj.init()
        obj.regist(self)
        if obj.has_prev():
            self.prevs.append(obj.prev)
        if obj.has_deal():
            self.deals.append(obj.deal)
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
    def __init__(self):
        self.index = 0
        self.deals = []
        self.prevs = []
    def load(self, reader):
        if type(reader) in [str, bytes]:
            #print(f"try str, {len(reader)}")
            buff = buffer.StrBuffer(reader)
            s = reader.replace(" ", "")
            queue = Stack(len(s)+1)
        else:
            buff = buffer.Buffer(reader)
            queue = []
        _pos = pos.PosCal()
        self.pos = _pos
        self.buffer = buff
        self.queue = queue
        import time
        crr = time.time()
        while self.do(self.prevs, buff, queue, _pos):
            pass
        now = time.time()
        #print(f"prev time: {now - crr}, prevs: {len(self.prevs)}, queue: {len(queue)}")
        #stack = []
        stack = Stack(len(queue))
        #stack = []
        crr = time.time()
        ns = 0
        while self.do(self.deals, queue, stack):
            ns = max(len(stack), ns)
            pass
        now = time.time()
        #print(f"deal time: {now - crr}, deals: {len(self.deals)}, stack: {ns}")
        if len(stack)==0:
            raise Exception("ERROR not data")
        for _item in stack:
            if not _item.check(is_val=1):
                print(f"err item: {_item}")
                raise exp.FormatExp("format error found", _item.pos)
        if len(stack)==1:
            return stack[0].val
        else:
            return [it.val for it in stack]

pass
