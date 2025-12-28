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
    [0,0,0,a=0,b=1,c=2]
]
"""
obj = xf.loadx(s)
print("obj")
print(obj)

rst = xf.dumpx(obj)
print("rst:")
print(rst)
print("\n")
rst = xf.dumpx(obj,format=1)
print("rst:")
print(rst)
print("\n")
rst = xf.dumpx(obj,format=1, not_format_height=2)
print("rst:")
print(rst)
print("\n")
rst = xf.dumpx(obj,format=1, not_format_height=2,json_format=1)
print("rst:")
print(rst)
print("\n")

obj = xf.loadx(rst)
print(obj)