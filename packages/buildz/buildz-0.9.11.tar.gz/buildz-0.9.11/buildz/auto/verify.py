#

from ..tools import *
from buildz.ioc import wrap
@wrap.obj(id="verify")
@wrap.obj_args("ref, log", "ref, cache.modify")
class Verify(Base):
    def init(self, log, upd):
        self.log = log.tag("Verify")
        self.upd = upd
        self.opts = {}
        self.opts[">"] = self.make_val_cmp(lambda val,v:val>v)
        self.opts["<"] = self.make_val_cmp(lambda val,v:val<v)
        self.opts[">="] = self.make_val_cmp(lambda val,v:val>=v)
        self.opts["<="] = self.make_val_cmp(lambda val,v:val<=v)
        self.opts["="] = self.eq
        self.opts["!="] = self.neq
    def eq(self, val, v):
        if type(val)!=type(v):
            if type(val)==str or type(v)==str:
                return str(val)==str(v)
        return val==v
    def neq(self, val, v):
        if type(val)!=type(v):
            if type(val)==str or type(v)==str:
                return str(val)!=str(v)
        return val!=v
    def make_val_cmp(self, opt):
        def fc(val, v):
            if val is None:
                return False
            if type(val)==str:
                val = float(val)
            if type(v)==str:
                v = float(v)
            return opt(val, v)
        return fc
    def match(self, v, val, result, data):
        tp,v = v
        if tp in self.opts:
            return self.opts[tp](val,v)
        if tp=="eval":
            return eval(v)
        elif tp == "exec":
            exec(v)
            return self.val
        else:
            err = f"not impl match type: {tp}"
            self.log.error(err)
            raise Exception(err)
    def call(self, data, fc=None):
        data = self.upd(data)
        note = xf.g(data, note=data)
        result = xf.g(data, result = {})
        vs = xf.g(data, verify=[])
        for it in vs:
            if type(it)==str:
                it = xf.loads(it)
            k,v=it
            bak = v
            if k == "$":
                if type(v)!=list:
                    v = ["eval", v]
                val = None
            else:
                val = xf.gets(data, k.split("."))
            if type(v)!=list:
                v = ["=", v]
            jg = self.match(v, val, result, data)
            if not jg:
                self.log.error(f"verify failed in {note}, key: '{k}', match: {bak}, val: {val}")
                return False
        if fc is None:
            return True
        return fc(data)

pass
