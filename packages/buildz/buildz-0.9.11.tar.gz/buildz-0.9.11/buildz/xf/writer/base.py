
class BaseDeal:
    def fmt(self, s, num, spc = " "):
        spc = self.like(spc, s)
        spc = spc*num
        et = self.like("\n", s)
        arr = s.split(et)
        arr = [spc+k for k in arr]
        rs = et.join(arr)
        return rs
    def __call__(self, queue, conf):
        return self.deal(queue, conf)
    def deal(self, queue, conf):
        "impl"
        return None
    def sp(self):
        return super(self.__class__, self)
    def regist(self, mgs):
        if self._id is None:
            self._id = mgs.regist()
    def id(self):
        return self._id
    def same(self, s, target):
        return self.like(s, target) == target
    def like(self, s, target):
        if type(target) ==type(s):
            return s
        if type(s)==str:
            return s.encode()
        return s.decode()
    def __str__(self):
        return "BaseDeal"
    def __repr__(self):
        return str(self)
    def __init__(self, *argv, **maps):
        self._id = None
        self.init(*argv, **maps)
    def init(self, *argv, **maps):
        pass