#

from .lst import FcFpsListener
from .. import Base, xf, dz, pathz, pyz
import os, sys
class Runner(Base):
    def init(self, fp, lst):
        fp = os.path.abspath(fp)
        self.dp = os.path.dirname(fp)
        self.path = pathz.Path(fp=self.dp)
        self.fp = fp
        self.lst = lst
        self.lst.set_update(self.update)
        self.lst.set_deal_exp(self.deal_exp)
        self.reset()
    def reset(self,last_update=False):
        conf = xf.loadf(self.fp)
        fps, target, dp = dz.g(conf, fps = [], run=None, dp="")
        dp = self.path.fp(dp)
        sys.path.append(dp)
        self.path.set("sc", dp)
        fps = [self.path.sc(fp) for fp in fps]
        self.lst.clean()
        self.lst.add(self.fp, last_update)
        [self.lst.add(fp, last_update) for fp in fps]
        self.target=target
    def update(self, fps):
        self.reset(True)
        fc = pyz.load(self.target)
        fc()
    def deal_exp(self, exp, fmt_exc):
        print(f"exp: {exp}")
        print(f"traceback: \n{fmt_exc}")

def test():
    fp = sys.argv[1]
    lst = FcFpsListener()
    runner = Runner(fp, lst)
    lst.run()

pass
pyz.lc(locals(), test)