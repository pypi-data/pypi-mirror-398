
from .. import xf, pyz, dz
from .sc import ScRunner
def test():
    import sys
    fp = sys.argv[1]
    conf = xf.loadf(fp)
    dz.s(conf, run="buildz.db.subrun.test")
    ScRunner.process_update(conf)

pass

pyz.lc(locals(), test)