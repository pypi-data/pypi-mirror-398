#

from .pool import *
import threading
class FcTask(Task):
    def init(self, fc, args=[], maps={}, fc_exp = None):
        self.fc = fc
        self.args = args
        self.maps = maps
        self.fc_exp = fc_exp
    def run(self):
        return self.fc(*self.args, **self.maps)
    def deal_exp(self, exp, traceback_exp):
        if self.fc_exp is not None:
            return self.fc_exp(exp, traceback_exp)
        print("FcTask exp:", exp)
        print("traceback:", traceback_exp)
class SimpleTasks(Tasks):
    def init(self, wait_sec = 0.1):
        self.condition = threading.Condition()
        self.tasks = []
        self.wait_sec = wait_sec
        self.wait_count=0
    def waits(self):
        return len(self.tasks)
    def add(self, task):
        with self.condition:
            self.tasks.append(task)
            if self.wait_count>0:
                self.condition.notify(1)
    def pop(self):
        with self.condition:
            if len(self.tasks)==0:
                self.wait_count+=1
                self.condition.wait(self.wait_sec)
                self.wait_count-=1
            if len(self.tasks)==0:
                return None
            return self.tasks.pop(0)
class RangeManager(WorkerManager):
    def init(self, vmin=0, vmax=-1):
        self.min = vmin
        self.max = vmax
    def change(self, workers, tasks, first_call):
        waits = tasks.waits()
        curr = len(workers)
        if curr<self.min:
            return self.min-curr
        if self.max>0 and curr>self.max:
            return self.max-curr
        frees = len([wk for wk in workers if wk.wait_count>1])
        needs = waits-frees
        rst = curr+needs
        if needs==0:
            return 0
        if needs>0:
            if self.max>0 and rst>self.max:
                needs = self.max-curr
            return needs
        else:
            if rst<self.min:
                needs = self.min-curr
            return needs

pass            
