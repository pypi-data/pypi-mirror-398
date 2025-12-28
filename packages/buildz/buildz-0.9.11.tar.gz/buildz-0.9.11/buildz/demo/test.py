#coding=utf-8
from buildz import xf, argx, pyz, ioc, fz
from os.path import dirname, join
args, maps = argx.fetch()
en = argx.get(maps, 'en', 0)
text_sfx = "" if not en else ".en"
class Help:
    def __init__(self, dp, fp):
        fp = join(dp, fp)
        self.obj = xf.loads(xf.fread(fp))
        self.text = self.obj['text'+text_sfx]
    def deal(self):
        print(self.text)

pass
class Deal:
    def __init__(self, conf, deals, default):
        self.deals = {}
        self.default = default
        for md in deals:
            self.deals[md] = {}
            refs = deals[md]
            for key in refs:
                ref = refs[key]
                obj = conf.get(ref)
                self.deals[md][key] = obj
    def run(self):
        if len(args)==0:
            return self.default.deal()
        md = args[0]
        help = "h" in maps or "help" in maps
        key = "deal" if not help else "help"
        if md not in self.deals:
            return self.default.deal()
        obj = self.deals[md][key]
        obj.deal()

pass
dp = dirname(__file__)
import time
def test():
    print(f"start\n{'='*30}")
    args, maps = argx.fetch()
    curr = time.time()
    fps = fz.search(join(dp, 'res', 'conf'), ".*\.js")
    confs = ioc.build()
    confs.add_fps(fps)
    confs.get("run")
    sec = time.time()-curr
    ps = f"{'='*30}\nPS: 这只是个使用展示demo，代码在buildz.demo里，可供参考，运行耗时: {sec}"
    if en:
        ps = f"{'='*30}\nPS: just an demo show used of buildz module, demo codes is in buildz.demo, run time cost: {sec}"
    print(ps)

pass
    
