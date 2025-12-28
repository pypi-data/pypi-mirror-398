
import inc, time, os
from multiprocessing import Process
import subprocess
print('test x')
def fc():
    while True:
        print(f"subprocess: {os.getpid()} running")
        time.sleep(1.0)
def test():
    try:
        inc.fc()
        print("xxxtestxxxxxxxx", __name__)
        return
        subprocess.run("python inc.py")
        print("done subprocess")
        p = Process(target=fc, daemon=True)
        print("process")
        p.start()
        print("process start")
        while True:
            print(f"process {os.getpid()} running")
            time.sleep(0.5)
            #p.kill()
    finally:
        pass
pass
