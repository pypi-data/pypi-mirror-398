#

from buildz import xf

s = r"""
a=0
b=1
c={
    a=2,
    d=3
    e=4
    f=5
    g=6
}
h=[
    {a=0,b=1,c=2}
    asdf
    'haha'
    [0,0,0]
]
"""
obj = xf.loads(s)
print("obj")
print(obj)

rst = xf.dumps(obj)
print("rst:")
print(rst)
print("\n")
rst = xf.dumps(obj,format=1)
print("rst:")
print(rst)
print("\n")
rst = xf.dumps(obj,format=1, not_format_height=2)
print("rst:")
print(rst)
print("\n")
rst = xf.dumps(obj,format=1, not_format_height=2,json_format=1)
print("rst:")
print(rst)
print("\n")

def build(n=30, m=6, l=6, val = 123):
    _arr = [val]
    print("test A")
    for i in range(n):
        _arr = [list(_arr)]
    print("test B")
    _map = {}
    for i in range(m):
        _map[i] = dict(_map)
    print("test C")
    rst = []
    for i in range(l):
        rst.append([_arr,_map])
    return rst

pass
from buildz.xf import write, writez
from buildz import xf
from buildz.tz import time as timez
timecost = timez.timecost(out_sec = 1)
dumpz = timecost(writez.dumps)
dump = timecost(write.dumps)
val = xf.loadf(r"D:\rootz\python\lx\pyz\docs\工作\zrecords\process.js")
obj = build(100,12,12, val)
rst, secz = dumpz(obj,format=1)
rst, sec = dump(obj,format=1)
print(f"writez = {secz/sec} write")
print(f"write = {sec/secz} writez")
#print("obj:", rst)