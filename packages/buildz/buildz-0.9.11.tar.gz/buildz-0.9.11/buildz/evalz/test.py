#

from buildz import evalz, xf
class VarEval(evalz.Eval):
    def init(self, key):
        self.key = key
    def call(self, obj):
        return obj[self.key]
class VarBuild(evalz.Build):
    def call(self, data):
        key = data['data'][0]
        return VarEval(key)
vb = VarBuild()
builder = evalz.EvalBuilder.Make().set("v", vb).set("var", vb)

conf = xf.loads(r"""
&, 
['=', [v, name], test]
['=', [v, value], 1024]
""")

eval = builder(conf)
data = xf.loads(r"""
name=test
value = 1024
""")
print(eval(data))

"""
python -m buildz.evalz.test

"""