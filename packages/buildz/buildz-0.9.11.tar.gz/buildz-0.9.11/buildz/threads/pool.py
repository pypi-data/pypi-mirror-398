
import threading,time
from .. import Base
class Task(Base):
    def run(self):
        pass
    def deal_exp(self, exp, traceback_exp):
        pass
class BasePool(Base):
    def check_run(self):
        return False
    def get_task(self):
        return None
class Worker(Base):
    def id(self):
        return threading.get_ident()
    def init(self, pool):
        self.pool = pool
        self.running = False
        self.do_run = False
        self.wait_time=0
        self.wait_count = 0
        self.work_time=0
        self.th = None
    def start(self):
        assert self.th is None
        self.th = threading.Thread(target=self.run,daemon=True)
        self.th.start()
    def safe_stop(self):
        self.do_run=False
    def work_rate(self):
        return self.work_time/(self.work_time+self.wait_time+1e-4)
    def run(self):
        self.wait_time=0
        self.work_time=0
        self.wait_count=0
        self.running = True
        self.do_run = True
        while self.do_run and self.pool.check_run():
            start = time.time()
            task = self.pool.get_task()
            task_start = time.time()
            if task is None:
                self.wait_time+=task_start-start
                self.wait_count+=1
                continue
            self.wait_count=0
            try:
                task.run()
            except Exception as exp:
                import traceback
                try:
                    task.deal_exp(exp, traceback.format_exc())
                except Exception as _exp:
                    print(f"deal_exp on {exp} get except: {_exp}")
            finish = time.time()
            self.wait_time+=task_start-start
            self.work_time+=finish-task_start
        self.running = False
        self.th = None

pass
class Tasks(Base):
    def waits(self):
        return 0
    def add(self, task):
        pass
    def pop(self):
        return None
class WorkerManager(Base):
    def change(self, workers, tasks, first_call=False):
        return 0

pass
class Pool(BasePool):
    def check_run(self):
        return self.running
    def get_task(self):
        return self.tasks.pop()
    def init(self, tasks, manager):
        self.running = False
        self.workers = []
        self.stops = []
        self.manager = manager
        self.tasks = tasks
    def start(self):
        if self.running:
            return
        self.running = True
        for wk in self.workers:
            wk.safe_stop()
            self.stops.append(wk)
        self.workers = []
        self.clean_stops()
        self.change_workers(True)
    def change_workers(self, first=False):
        num = self.manager.change(self.workers, self.tasks, first)
        if num==0:
            return
        if num>0:
            for i in range(num):
                worker = Worker(self)
                worker.start()
                self.workers.append(worker)
        else:
            for i in range(-num):
                worker = self.workers.pop()
                worker.safe_stop()
                self.stops.append(worker)
    def clean_stops(self):
        self.stops = [wk for wk in self.stops if wk.running]
    def check_finish(self):
        for k in self.workers:
            if k.running:
                return False
        for k in self.stops:
            if k.running:
                return False
        return True
    def stop(self):
        self.running = False
    def add_task(self, task):
        self.tasks.add(task)
        if self.running:
            self.change_workers()

pass