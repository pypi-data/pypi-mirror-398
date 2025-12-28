
from buildz.threads import *
import time
tasks = SimpleTasks()
manager = RangeManager(1,3)
pool = Pool(tasks, manager)
print(pool)
import threading,time
def test(sec):
    _id = threading.get_ident()
    print(f"thread {_id} [start]")
    time.sleep(sec)
    print(f"thread {_id} stop")

pass
pool.add_task(FcTask(test, [0.5]))
pool.start()
for i in range(10):
    pool.add_task(FcTask(test, [0.5]))


time.sleep(2.0)