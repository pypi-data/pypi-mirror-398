#coding=utf-8
#from .read import loads
from .readz import loads, loadx
import sys
def fetch(argv = None,base=1):
    if argv is None:
        argv = sys.argv[base:]
    argv = [str(k) for k in argv]
    s = " ".join(argv)
    s = s.strip()
    return loadx(s, out_args=True, colon = False)
    lrs = [["",""]]
    if len(s)==0:
        return None
    if s[0] not in "([{":
        lrs = ["{}", "[]"]
    for l,r in lrs:
        x = l+s+r
        try:
            return loads(x)
        except:
            pass
    raise Exception("unable to fetch params")

pass
# python -m buildz.xf {a:b}
def test():
    rst = fetch()
    print(f"cmd params: {rst}")

pass
