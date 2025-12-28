#
from .. import evalz,xf,Base

class VarEval(evalz.Eval):
    def init(self, key, stype = 'list'):
        self.key = key
        self.stype = stype
    def call(self, obj):
        args, maps = obj.args, obj.maps
        if self.stype=='list':
            return args[self.key]
        return maps[self.key]
class VarBuild(evalz.Build):
    def init(self, stype="list"):
        super().init()
        self.stype = stype
    def call(self, data):
        return VarEval(data['data'][0], self.stype)
lb = VarBuild('list')
db = VarBuild('dict')

class SizeEval(evalz.Eval):
    def init(self, key):
        self.key = key
    def call(self, obj):
        args, maps = obj.args, obj.maps
        if self.key in 'l,list,args'.split(","):
            return len(args)
        elif self.key in 'd,dict,maps'.split(","):
            return len(maps)
        assert 0
class SizeBuild(evalz.Build):
    def call(self, data):
        return SizeEval(data['data'][0])
class UnitEval(evalz.Eval):
    def init(self, encape):
        self.encape = encape
    def call(self, obj):
        return self.encape()
class UnitBuild(evalz.Build):
    def init(self, unit):
        super().init()
        self.unit = unit
    def call(self, data):
        conf = [data['type']]+data['data']
        encape, _, find = self.unit.get_encape(conf)
        assert find
        return UnitEval(encape)

sb = SizeBuild()
evalBuilder = evalz.EvalBuilder.Make().set(["l","list","args"], lb).set(['d','dict','maps'], db).set("size,len".split(","), sb)
