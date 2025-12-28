
from buildz import Base
import os,time, traceback
class FpsListener(Base):
    def init(self, wait_sec=0.1):
        self.fps = {}
        self.wait_sec = wait_sec
        self.running=False
    def set_wait(self, wait):
        self.wait_sec = wait
    def update(self, fps):
        pass
    def deal_exp(self, exp, format_exc):
        pass
    def add(self, fp, last_update=False):
        if type(last_update)==bool:
            if last_update:
                last_update = os.path.getmtime(fp)
            else:
                last_update = 0
        self.fps[fp] = last_update
    def clean(self):
        self.fps = {}
    def reset(self, fps, last_update=False):
        self.clean()
        for fp in fps:
            self.add(fp, last_update)
    def run(self):
        self.running = True
        while self.running:
            self.work()
            time.sleep(self.wait_sec)
    def work(self):
        upds = []
        for fp,sec in self.fps.items():
            curr = os.path.getmtime(fp)
            if curr!=sec:
                upds.append(fp)
            self.fps[fp]=curr
        if len(upds)==0:
            return
        try:
            self.update(upds)
        except Exception as exp:
            trs = traceback.format_exc()
            try:
                self.deal_exp(exp, trs)
            except Exception as exp1:
                print(f"exp in deal_exp({exp}): {exp1}")
                traceback.print_exc()

pass

class FcFpsListener(FpsListener):
    def init(self,wait_sec=0.1):
        super().init(wait_sec)
        self.fc_update = None
        self.fc_exp = None
    def set_update(self, fc):
        self.fc_update = fc
    def set_deal_exp(self, fc):
        self.fc_exp = fc
    def update(self, fps):
        return self.fc_update(fps)
    def deal_exp(self, exp, fmt_exc):
        return self.fc_exp(exp, fmt_exc)

pass