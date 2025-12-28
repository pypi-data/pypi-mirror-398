#
from .ioc.decorator import decorator, ns
from .ioc_deal import init
#print(f"decorator.fcs: {decorator.fcs}")
locals().update(decorator.fcs)
from buildz import fz
import os
def pkg(fp):
    r = fp.rfind(".")
    if r>0:
        fp = fp[:r]
    fp = fp.replace("\\", "/")
    fp = fp.replace("//", "/")
    fp = fp.replace("/", ".")
    while len(fp)>0 and fp[0]==".":
        fp = fp[1:]
    __import__(fp)

pass
def imports(dp=".", pts=".*\.py$", pfx=""):
    """
    not include test: r"^(?!.*(?:test|bak)).*\.py$"
    find filepath by dirpath(dp) and pattern(pts), 
    import:
    filepath = ".".join(filepath.split(".")[:-1])
    filepath = filepath[len(dp):]
    package = pfx+"." if pfx!="" else "")+(filepath.replace("/", "."))
    """
    dp = os.path.abspath(dp)
    fps = fz.search(dp, pts)
    fps = [pfx+"/"+fp[len(dp):] for fp in fps]
    for fp in fps:
        pkg(fp)

pass
includes=imports