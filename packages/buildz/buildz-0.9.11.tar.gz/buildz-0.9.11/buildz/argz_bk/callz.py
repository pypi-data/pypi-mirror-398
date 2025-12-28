from buildz import Base, xf
from . import argz
from . import build
from . import evalx
class Fc(Base):
    def str(self):
        return str(self.fc)
    def init(self, fc=None):
        self.fc = fc
    def call(self, args, maps):
        return self.fc(*args, **maps)
    @staticmethod
    def make(fc):
        if isinstance(fc, Fc):
            return fc
        return Fc(fc)
class RetFc(Fc):
    def call(self, args, maps):
        return args, maps
class ArgsCall(Fc):
    def init(self, fc, args=None, name = None):
        fc=self.make(fc)
        if name is None:
            name = str(fc)
        self.name = name
        self.fc = fc
        self.args = args
    def call(self, args, maps):
        if self.args is not None:
            args, maps = self.args(args, maps)
        try:
            return self.fc(args, maps)
        except argz.ArgExp as exp:
            if self.args is not None:
                exp = self.args.deal_exp(exp)
            raise exp
class Calls(Fc):
    def str(self):
        return "argz.Calls"
    def init(self, fcs = None, args=None, name = None):
        if name is None:
            name = "argz.calls"
        self.name = name
        if fcs is None:
            fcs = []
        self.fcs = fcs
        self.args = args
    def add(self, fc):
        fc=self.make(fc)
        self.fcs.append(fc)
    def call(self, args, maps):
        val = None
        if self.args is not None:
            args, maps = self.args(args, maps)
        try:
            for fc in self.fcs:
                val = fc(args, maps)
            return val
        except argz.ArgExp as exp:
            if self.args is not None:
                exp = self.args.deal_exp(exp)
            raise exp
class EvalCall(Fc):
    def init(self, fc, eval=None, name = None):
        fc=self.make(fc)
        if name is None:
            name = str(fc)
        self.eval = eval
        self.fc = fc
        self.name = name
    def call(self, args, maps):
        if self.eval is not None:
            if not self.eval([args, maps]):
                return None
        return self.fc(args, maps)
class CallsBuild(build.Build):
    def call(self, conf):
        ctype = xf.g(conf, type=None)
        if ctype != "calls":
            return None
        calls = xf.g(conf, calls = [])
        if len(calls)==0:
            return None
        calls = [self.builder.get_conf(conf) for conf in calls]
        return Calls(calls)
class FcBuild(build.Build):
    def call(self, conf):
        ctype = xf.g(conf, type=None)
        if ctype != "call":
            return None
        src = xf.g(conf, src = None)
        fc = self.builder.get_var(src)
        return Fc(fc)
class RetBuild(build.Build):
    def call(self, conf):
        ctype = xf.g(conf, type=None)
        if ctype != "ret":
            return None
        return RetFc()
class CallBuild(build.Build):
    def init(self):
        self.args = argz.ArrArgsBuild()
        self.eval = evalx.EvalBuild()
        self.fc = FcBuild()
        self.calls = CallsBuild()
        self.ret = RetBuild()
        super().init(self.args, self.eval, self.fc, self.calls)
    def call(self, conf):
        args = self.args(conf)
        judges = self.eval(conf)
        fc = self.fc(conf)
        calls = self.calls(conf)
        ret = self.ret(conf)
        bfc = fc is None
        bcls = calls is None
        bret = ret is None
        assert (bfc+bcls+bret)==2
        if fc is None:
            fc = calls
        if fc is None:
            fc = ret
        if args is not None:
            fc = ArgsCall(fc, args)
        if judges is not None:
            fc = EvalCall(fc, judges)
        return fc
class CallBuilder(build.Builder):
    def init(self, key_id = "id"):
        super().init(CallBuild(), key_id)
