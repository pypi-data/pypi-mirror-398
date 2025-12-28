#coding=utf-8
from . import base
import termios
import sys
import ctypes
import select
std = ctypes.cdll.LoadLibrary(None)
class Getch(base.Getch):
    def __init__(self, timeout =0.01, cnt = 3):
        attr = termios.tcgetattr(sys.stdin.fileno())
        bak = list(attr)
        attr[3] = attr[3] & ~(termios.ICANON|termios.ECHO)
        self.bak = bak
        self.attr = attr
        self.sec = timeout
        self.cnt = cnt
    def _open(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.attr)
    def _close(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.bak)
    def call(self):
        c = std.getchar()
        if c==27:
            next = False
            # 没用
            for i in range(self.cnt):
                a,_b,_c = select.select([sys.stdin.fileno()], [], [], self.sec)
                if len(a)>0:
                    next = True
                    break
            if next:
                rst = [c]
                rst.append(std.getchar())
                rst.append(std.getchar())
                return rst
        return c

pass
