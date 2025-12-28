

from buildz import xf
a = xf.loads(r'"asdf\n\r\0x"')
print(a)
b = xf.loads(r"asdftest\n\r")
print(b)
