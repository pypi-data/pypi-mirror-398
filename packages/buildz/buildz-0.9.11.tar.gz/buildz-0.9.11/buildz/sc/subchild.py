#

from . import subrun
from .. import xf, pyz
def test():
    import sys
    fp = sys.argv[1]
    conf = xf.loadf(fp)
    subrun.Runner.process_update(conf)

pass

pyz.lc(locals(), test)