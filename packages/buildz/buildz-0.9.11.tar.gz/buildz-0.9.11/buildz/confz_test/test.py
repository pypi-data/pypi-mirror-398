
from buildz import confz, pathz, pyz
import os,sys

dp = os.path.dirname(__file__)

path = pathz.Path()
path.set(None, dp)
def test():
    sys_conf = confz.get_sys_conf(path("argx.js"))
    confz.run(dp, "test.js", sys_conf)

pass

def xtest(conf):
    print(f"[DEBUG] xtest:", conf)

pass

pyz.lc(locals(), test)

'''
python -m buildz.confz_test.test

python -m buildz.confz_test.test -v0
'''