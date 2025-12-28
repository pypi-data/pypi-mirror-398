#

from buildz.argz import conf_argz as argz
from buildz.tls import *
conf = xf.loads(r"""
#range=(0,12,3)
range=(1,12,1)
args: {
    0:[0,0]
}
maps: {
    a={
        default: test
    }
}
""")
def test():
    args = [0,1,2]
    maps = {'a':'b','c':'d'}
    bd = argz.FullArgsBuilder()
    obj = bd(conf)
    args, maps = obj.deal(args, maps)
    print(f"obj: {obj}")
    print(f"args: {args}, maps: {maps}")
    pass

pass

pyz.lc(locals(),test)