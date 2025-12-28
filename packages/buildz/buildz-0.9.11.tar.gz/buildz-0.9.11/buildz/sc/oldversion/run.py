#

from .lst import FcFpsListener
from .. import Base, xf, dz, pathz, pyz
import os, sys
from multiprocessing import Process
class TestFc:
    def __init__(self, fc):
        self.fc = fc
    def __call__(self, *a, **b):
        print(f"[TESTZ] call: {self.fc}(*{a}, **{b})")
        self.fc(*a,**b)
class Test:
    def __init__(self, file):
        self.file = file
    # def write(self):
    #     pass
    def __getattr__(self, key):
        fc = getattr(self.file, key)
        print(f"[TESTZ] get: {key} = {fc}")
        if not callable:
            return fc
        #return getattr(self.file, key)
        return TestFc(fc)
class Runner(Base):
    def init(self, fp, lst):
        fp = os.path.abspath(fp)
        self.dp = os.path.dirname(fp)
        self.path = pathz.Path(fp=self.dp)
        self.fp = fp
        self.lst = lst
        self.lst.set_update(self.update)
        self.lst.set_deal_exp(self.deal_exp)
        self.process = None
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
        self.conf = conf
    @staticmethod
    def process_update(conf):
        target, sc_path, args, stdin, stdout, stderr = dz.g(conf, run=None,sc_path=__file__, args=[], stdin = "std", stdout = "std", stderr="std")
        encoding = dz.g(conf, encoding="utf-8")
        import sys, os
        args = [sc_path]+args
        sys.argv = args
        stds = [stdin, stdout, stderr]
        stds = [list(k) if type(k) in (list, tuple) else [k] for k in stds]
        modes = "rww"
        for std, mode in zip(stds, modes):
            if len(std)<3:
                std.append(mode)
        objs = []
        files = {}
        for std in stds:
            do_close = False
            if std[0]=='std':
                obj = sys.stdin if std[-1]=='r' else sys.stdout
            elif std[0]=='str':
                obj = io.StringIO(std[1])
            else:
                if std[1] not in files:
                    files[std[1]] = open(std[1], std[-1], encoding=encoding)
                obj = files[std[1]]
            objs.append(obj)
        #bak = [sys.stdin, sys.stdout, sys.stderr]
        sys.stdin = objs[0]
        sys.stdout = objs[1]
        sys.stderr = objs[2]#Test(objs[2])#objs[2]
        #print(f"stdin: {sys.stdin}, stdout: {sys.stdout}, stderr: {sys.stderr}")
        #print(f"files: {files}")
        try:
            #print(f"start process: {os.getpid()}")
            fc = pyz.load(target)
            if callable(fc):
                fc()
        except Exception as exp:
            #print(f"exp:", exp)
            #print(f"exp in process: {os.getpid()}")
            raise exp
        finally:
            #print(f"done process: {os.getpid()}, {objs[2].closed}")
            for fp, f in files.items():
                f.flush()
            #sys.stdout = bak[1]
    def update(self, fps):
        if self.process is not None:
            if self.process.is_alive():
                self.process.kill()
            self.process = None
        self.reset(True)
        p = Process(target = self.process_update,args=[self.conf], daemon=True)
        p.start()
        self.process = p
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