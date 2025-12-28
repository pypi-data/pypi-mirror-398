from buildz import argz,xf,Base,evalz,pathz
import sys,os

path = pathz.Path()
path.set("res", path(path.dir(__file__), "tests"))
conf = xf.loadf(path.res("conf.js"))

def search(dp, filepath = None, content = None):
    print(f"call in search: ({dp}, {filepath}, {content})")
    return f"call in search {dp}"

pass


mg = argz.CallBuilder().var("search", search)
fc = mg(conf)

ins = xf.args(base=0)
args, maps = ins.args, ins.maps

rst = fc(args, maps)
print(f"rst: {rst}")
'''
python -m buildz.argz.test search /d/rootz
python -m buildz.argz.test search /d/rootz f=asf c=test
'''