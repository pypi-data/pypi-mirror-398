#coding=utf-8

from buildz import pyz
getch = None
if pyz.is_windows:
    from . import win
    getch = win.Getch()
else:
    from . import lx
    getch = lx.Getch()

pass
def open():
    global getch
    return getch.open()

pass

def close():
    global getch
    getch.close()

pass