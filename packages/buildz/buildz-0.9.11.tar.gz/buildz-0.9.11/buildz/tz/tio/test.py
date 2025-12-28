#coding=utf-8

from buildz.tz import getch
getch.init()
while True:
    c = getch()
    print(f"getch: {c}")
    if c==b'q'[0]:
        break

pass
getch.close()
