from buildz import argz,xf,Base,evalz,pathz
import sys,os

path = pathz.Path()
path.set("res", path(path.dir(__file__), "tests"))
conf = xf.loadf(path.res("conf.js"))
conf=xf.loads(r"""
type=ret
maps={
    spt: {
        src: [(env, spt), d]
        default: 1
        value: '.'
    }
    eglobal: {
        src: [(env, global), d]
        default:1
        value: true
    }
}
""")

mg = argz.CallBuilder()
fc = mg(conf)

data = xf.loads(r"""
args=[]
maps={
    env: {
        spt: x
    }
}
""")
args = xf.g(data, args=[])
maps = xf.g(data, maps={})

rst = fc(args, maps)
print(f"rst: {rst}")
'''
python -m buildz.argz.testx
python -m buildz.argz.test search /d/rootz f=asf c=test
'''
