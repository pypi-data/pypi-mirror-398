#coding=utf-8
import ctypes
from . import base
class Getch(base.Getch):
    def call(self):
        return ctypes.cdll.msvcrt._getch()

pass
