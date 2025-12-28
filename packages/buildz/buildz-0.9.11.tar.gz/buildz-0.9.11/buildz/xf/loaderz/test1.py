

from buildz import xf
obj = xf.loads(r'"asdf\n\r\0x"')
print(obj)
obj = xf.loads(r"asdftest\n\r")
print(obj)
obj = xf.loads("{}")
print(obj)
obj = xf.loads("{a:0,[]}")
print(obj)
