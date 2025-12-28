
from buildz.ioc import wrap
x = wrap.ns("test")
@wrap.obj(id='x')
class A:
    pass

pass
@x.obj(id='y')
class B:
    pass

pass
from buildz import ioc
mg= ioc.build()
x = mg.get('x')
y = mg.get('test.y')
print(x)
print(y)

