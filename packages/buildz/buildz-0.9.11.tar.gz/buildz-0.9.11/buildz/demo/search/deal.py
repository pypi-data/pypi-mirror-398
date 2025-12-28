#coding=utf-8
from buildz import xf, argx, pyz, ioc, fz

from ..test import text_sfx, args, maps
class Deal:
    def deal(self):
        if len(args)<2:
            print("need params 1 to be dirpath")
            return
        dp = args[1]
        ct_fp = argx.get(maps, "f,file".split(","), None)
        ct = argx.get(maps, "c,content".split(","), None)
        depth = argx.get(maps, "d,depth".split(","), None)
        out_fp = argx.get(maps, "o,output".split(","), None)
        show = argx.get(maps, "s,show".split(","), False)
        prv = int(argx.get(maps, "p,prev".split(","), 10))
        aft = int(argx.get(maps, "a,aft".split(","), 10))
        shows = [prv, aft]
        if depth is not None:
            depth = int(depth)
        rst = fz.search(dp, ct_fp, ct, depth, show=show, shows=shows)
        l = len(rst)
        rs = "\n".join(rst)
        if out_fp is not None:
            with open(out_fp, 'w') as f:
                f.write(rs)
            print(f"result save in {out_fp}")
        else:
            print(rs)
        print(f"done search, find files: {l}")
    pass

pass
