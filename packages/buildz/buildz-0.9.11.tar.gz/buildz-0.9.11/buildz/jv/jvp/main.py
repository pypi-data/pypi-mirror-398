#
from . import jsc, defs, dm, rn, fcs
import re,sys, os
from buildz import fz, dz, xf, argx, pyz, Base
fetch =argx.Fetch(*xf.loads("[fp,ofp,left,right,spt],{f:fp,o:ofp,l:left,r:right,s:spt}"))
def test():
    conf = fetch()
    fp, ofp = dz.g(conf, fp=None,ofp=None)
    if ofp is None:
        i = fp.rfind(".")
        if i>0:
            ofp = fp[:i]+".java"
        else:
            ofp = fp
    left, right, spt = dz.g(conf, left='<<', right='>>', spt = '||')
    deals = jsc.DealCodes(left, right, spt)
    deals.add("default", defs.default)
    deals.add("domain", dm.domains)
    deals.add("rename", rn.renames)
    deals.add("methods", fcs.fcs)
    s = fz.read(fp).decode("utf-8")
    rs = deals.update(s).encode("utf-8")
    fz.write(rs, ofp)
    print("done to", ofp)

pass
fetch =argx.Fetch(*xf.loads("[dp,odp,left,right,spt],{d:dp,o:odp,l:left,r:right,s:spt}"))
def tests():
    conf = fetch()
    dp, odp = dz.g(conf, dp=None,odp=None)
    dp = dp or '.'
    odp = odp or dp
    print(f"dp:", dp, sys.argv)
    fs = fz.search(dp, '.*\.javap')
    print(fs)
    left, right, spt = dz.g(conf, left='<<', right='>>', spt = '||')
    deals = jsc.DealCodes(left, right, spt)
    deals.add("default", defs.defaults)
    deals.add("domain", dm.domains)
    deals.add("rename", rn.renames)
    deals.add("methods", fcs.fcs)
    for fp in fs:
        fn = fp
        if len(dp)>0:
            fn = fp[len(dp):]
            if fn[0] in "\\/":
                fn = fn[1:]
        #print(f"[TESTZ] fn:]: {fn}")
        #print(f"[TESTZ] odp: {odp}")
        ofp = os.path.join(odp, fn)
        i = ofp.rfind(".")
        if i>0:
            ofp = ofp[:i]+".java"
        else:
            ofp = ofp+".java"
        #print(f"[TESTZ] fp: {fp}")
        s = fz.read(fp).decode("utf-8")
        rs = deals.update(s).encode("utf-8")
        #print(f"[TESTZ] ofp: {ofp}")
        fz.write(rs, ofp)
    print("done to", odp)



pyz.lc(locals(), tests)

"""
python -m main Conf.javap
python -m main Utils.javap

python -m buildz.jv.jvp.main ../confz

"""