from buildz import Base, xf, pathz
import os
dp = os.path.dirname(__file__)
path = pathz.Path()
path.set("res", os.path.join(dp, "res"))
class Eval(Base):
    def call(self, obj):
        return True
class Build(Base):
    def init(self):
        self.builder = None
    def bind(self, builder):
        self.builder = builder
class FcEval(Eval):
    def init(self, fc, eval):
        self.eval = eval
        self.fc = fc
    def call(self, obj):
        return self.fc(self.eval(obj))
    @staticmethod
    def Make(fc):
        def f(eval):
            return FcEval(fc, eval)
        return f
class FcBuild(Build):
    def init(self, fc):
        self.fc = fc
    def call(self, data):
        data = data['data']
        data = self.builder(data[0])
        return self.fc(data)
    @staticmethod
    def Make(fc):
        def f():
            return FcBuild(fc)
        return f
class ListEval(Eval):
    def init(self, evals = None):
        if evals is None:
            evals = []
        self.evals = evals
    def add(self, eval):
        self.evals.append(eval)
    def list_call(self, obj):
        assert 0, "not impl"
    def call(self, obj):
        assert len(self.evals)>0, "empty list evals"
        return self.list_call(obj)
class FcListEval(ListEval):
    def init(self, fc, evals=None, num = -1):
        super().init(evals)
        self.fc = fc
        self.num = num
    def list_call(self, obj):
        if self.num >= 0:
            assert len(self.evals)==self.num
        rst = self.evals[0](obj)
        for eval in self.evals[1:]:
            val = eval(obj)
            rst = self.fc(rst, val)
        return rst
    @staticmethod
    def Make(fc, num=-1):
        def f(evals=None):
            return FcListEval(fc, evals, num)
        return f
class ListBuild(Build):
    def list_call(self, arr):
        assert 0, "not impl"
    def call(self, data):
        data = data['data']
        arr = [self.builder(it) for it in data]
        return self.list_call(arr)
class FcListBuild(ListBuild):
    def init(self, fc, num=-1):
        super().init()
        self.num =num
        self.fc = fc
    def list_call(self, arr):
        if self.num>=0:
            assert self.num==len(arr)
        return self.fc(arr)
    @staticmethod
    def Make(fc, num=-1):
        def f():
            return FcListBuild(fc, num)
        return f
AndEval = FcListEval.Make(lambda x,y:x and y)
AndBuild = FcListBuild.Make(AndEval)
OrEval = FcListEval.Make(lambda x,y:x or y)
OrBuild = FcListBuild.Make(OrEval)
XorEval = FcListEval.Make(lambda x,y:x != y)
XorBuild = FcListBuild.Make(XorEval)
EqualEval = FcListEval.Make(lambda x,y:x == y)
EqualBuild = FcListBuild.Make(EqualEval)
BiggerEval = FcListEval.Make(lambda x,y:x > y)
BiggerBuild = FcListBuild.Make(BiggerEval)
BiggerEqualEval = FcListEval.Make(lambda x,y:x >= y)
BiggerEqualBuild = FcListBuild.Make(BiggerEqualEval)
LittlerEval = FcListEval.Make(lambda x,y:x < y)
LittlerBuild = FcListBuild.Make(LittlerEval)
LittlerEqualEval = FcListEval.Make(lambda x,y:x<=y)
LittlerEqualBuild = FcListBuild.Make(LittlerEqualEval)
PatternEval = FcListEval.Make(lambda val, pt:len(re.findall(pt, val))>0, num=2)
PatternBuild = FcListBuild.Make(PatternEval, 2)
InEval = FcListEval.Make(lambda val, lst: val in lst, num=2)
class InBuild(Build):
    def call(self, data):
        data = data['data']
        assert len(data)==2
        val = self.builder(data[0])
        arr = [self.builder(it) for it in data[1]]
        return InEval([val, arr])
NotEval = FcEval.Make(lambda x: not x)
NotBuild = FcBuild.Make(NotEval)
class ValEval(Eval):
    def init(self, val):
        self.val = val
    def call(self, obj):
        return self.val
class ValBuild(Build):
    def call(self, data):
        data = data['data'][0]
        return ValEval(data)
default_builds = xf.loadf(path.res("default.js"))
class EvalBuilder(Base):
    """
        {
            type: and|or|xor|not|=|>|<|pt|...
            data: [
                {type: var, data: name}
                {type: val, data: 'test'}
            ]
        }
        eq(var(name),val(test))
    """
    def init(self, default_type = None):
        self._default_type = default_type
        self.builds = {}
        self._default_build = None
    def default_type(self, dtype):
        self._default_type = dtype
    def default_build(self, fc):
        self._default_build = fc
        return self
    def set(self, key, fc):
        if type(key) not in (list, tuple):
            key = [key]
        fc.bind(self)
        for k in key:
            self.builds[k] = fc
        return self
    def call(self, data):
        if type(data) not in (list, tuple, dict):
            data = [self._default_type, data]
        if type(data) in (list, tuple):
            data = {'type':data[0], 'data':data[1:]}
        if type(data['data']) not in (list, tuple, set):
            data['data'] = [data['data']]
        tp = data['type']
        if tp not in self.builds and self._default_build is not None:
            return self._default_build(data)
        assert tp in self.builds
        return self.builds[tp](data)
    @staticmethod
    def Make(arr=[], default_sets = True, default_type = 'const'):
        obj = EvalBuilder(default_type)
        if default_sets:
            for k, opts in default_builds.items():
                fc = globals()[k]()
                if type(opts) not in (list, tuple, set):
                    opts = [opts]
                for opt in opts:
                    obj.set(opt, fc)
        for fc, opts in arr:
            if type(opts) not in (list, tuple, set):
                opts = [opts]
            for opt in opts:
                obj.set(opt, fc)
        return obj

pass