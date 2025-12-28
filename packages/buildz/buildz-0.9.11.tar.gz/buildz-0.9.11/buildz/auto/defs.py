#
from ..tools import *
from buildz.ioc import wrap
@wrap.obj(id="defs")
@wrap.obj_args("ref, cache", "ref, log", "ref, cache.modify")
class Defs(Base):
    def init(self, cache, log, upd):
        self.cache = cache
        self.log = log.tag("Defs")
        self.upd = upd
    def update(self, s, defs, ignore=None):
        if type(s)==dict:
            rst = {}
            for k,v in s.items():
                if k == ignore:
                    continue
                k,v = self.update(k, defs), self.update(v, defs)
                rst[k] = v
            return rst
        elif type(s)==list:
            rst = []
            for v in s:
                v = self.update(v,defs)
                rst.append(v)
            return rst
        for k,v in defs.items():
            if k==s:
                s = v
                continue
            if type(k)!=str:
                continue
            if type(s)!=str:
                continue
            s = s.replace(k,str(v))
        return s
    def call(self, data, fc=None):
        defs = self.upd(xf.g(data, defs = {}))
        data = self.update(data, defs, "defs")
        data = self.upd(data)
        if fc is None:
            return True
        return fc(data)

pass


