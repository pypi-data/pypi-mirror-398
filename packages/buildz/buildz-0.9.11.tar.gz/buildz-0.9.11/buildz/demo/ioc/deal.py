#coding=utf-8
from buildz import xf, argx, pyz, ioc, fz

from ..test import text_sfx, args, maps
class Deal:
    def deal(self):
        if len(args)<2:
            print("need params 1 to be dirpath")
            return
        dp = args[1]
        sfx = argx.get(maps, ("s", "suffix"), "js")
        fps = fz.search(dp, f".*\.{sfx}$")
        confs = ioc.build()
        confs.add_fps(fps)
        id = argx.get(maps, ("i", "id"), "main")
        rst = confs.get(id)
        print(f"get {id}: {rst}")
        return rst

pass
