#coding=utf-8
from . import xf
class Cmd:
    def close(self):
        self.running = False
    def __init__(self, obj):
        self.running = False
        self.obj = obj
        self.tmp = None
        self.exits = "exit,close,quit".split(",")
    def __call__(self):
        self.run()
    def doc(self, *arr):
        if len(arr)>0:
            rfc = getattr(self.obj, arr[0])
        else:
            rfc = self.obj
        return rfc.__doc__
    def help(self, *arr):
        if len(arr)>0:
            rfc = getattr(self.obj, arr[0])
        else:
            rfc = self.obj
        help(rfc)
    def dir(self, *arr):
        if len(arr)>0:
            rfc = getattr(self.obj, arr[0])
        else:
            rfc = self.obj
        arr = rfc.__dir__()
        arr = [k for k in arr if k[:2]!="__"]
        return arr
    def dict(self, *arr):
        if len(arr)>0:
            rfc = getattr(self.obj, arr[0])
        else:
            rfc = self.obj
        return rfc.__dict__
    def get(self, *arr):
        if len(arr)>0:
            return getattr(self.obj, arr[0])
        return self.obj
    def set(self, key, val):
        setattr(self.obj,key, val)
        return getattr(self.obj, key)
    def run(self):
        self.running = True
        while self.running:
            s = input(":").strip()
            if s.strip()=="":
                continue
            if s in self.exits:
                break
            try:
                arr = xf.loads(s)
                if type(arr)!=list:
                    if type(arr)==dict:
                        rst = []
                        for k,v in arr.items():
                            rst+=[k,v]
                        arr = rst
                    else:
                        arr = [arr]
                fc = arr[0]
                if not hasattr(self.obj, fc):
                    fc = fc.split(".")[-1]
                    fc = getattr(self, fc)
                else:
                    fc = getattr(self.obj, fc)
                params = arr[1:]
                tmp = fc(*params)
                print(tmp)
            except Exception as exp:
                import traceback
                print(f"[CMD] error:{exp}")
                traceback.print_exc()

pass
