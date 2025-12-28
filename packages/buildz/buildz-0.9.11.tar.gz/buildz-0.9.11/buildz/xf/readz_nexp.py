
from .loaderz_nexp import mg, buffer, base
from . import file
import os
from .loaderz_nexp.deal import nextz, spt, strz, listz, setz, mapz, reval, lrval, listmapz
class BoolFc:
    def __init__(self, mg):
        trues = [mg.like(k) for k in ["true", "True", "1"]]   
        trues += [1,True] 
        falses = [mg.like(k) for k in ["false", "False", "0"]]
        falses += [0,False]
        self.trues = set(trues)
        self.falses = set(falses)
    def __call__(self, val):
        if val in self.trues:
            return True
        elif val in self.falses:
            return False
        else:
            raise Exception("unknown bool val")

pass
def build_lrval(mgs):
    bl = BoolFc(mgs)
    fcs = lrval.Fcs()
    fcs.set("float", float)
    fcs.set("f", float)
    fcs.set("int", int)
    fcs.set("i", int)
    fcs.set("bool", bl)
    fcs.set("bl", bl)
    fcs.set("null", lambda x:None)
    fcs.set("nil", lambda x:None)
    fcs.set("n", lambda x:None)
    mgs.add(lrval.LRValDeal("<",">",fcs))

pass
def build_val(mgs):
    mgs.add(reval.ValDeal("[\+\-]?\d+", int))
    mgs.add(reval.ValDeal("[\+\-]?\d*\.\d+", float))
    mgs.add(reval.ValDeal("[\+\-]?\d*(?:\.\d+)?e[\+\-]?\d+", float))
    mgs.add(reval.ValDeal("null", lambda x:None))
    mgs.add(reval.ValDeal("true", lambda x:True))
    mgs.add(reval.ValDeal("false", lambda x:False))

pass
g_mg = None
def build(as_bytes=False):
    global g_mg
    if g_mg is not None and g_mg.as_bytes == as_bytes:
        return g_mg
    mgs = mg.Manager(as_bytes)
    mgs.add(setz.SetDeal(':'))
    mgs.add(setz.SetDeal('='))
    mgs.add(spt.PrevSptDeal(",",1))
    mgs.add(spt.PrevSptDeal(';',1))
    mgs.add(spt.PrevSptDeal('\n'))
    build_lrval(mgs)
    mgs.add(listz.ListDeal("(", ")"))
    mgs.add(listz.ListDeal("[", "]"))
    mgs.add(mapz.MapDeal("{", "}"))
    build_val(mgs)
    #1,0,0,1: 没引号当r"..."
    #1,0,1,1: 没引导当"..."
    mgs.add(strz.PrevStrDeal("r'''","'''",0,0,0))
    mgs.add(strz.PrevStrDeal('r"""','"""',0,0,0))
    mgs.add(strz.PrevStrDeal("r'","'",1,0,0,1))
    mgs.add(strz.PrevStrDeal('r"','"',1,0,0))
    mgs.add(strz.PrevStrDeal("###","###",0,1))
    mgs.add(strz.PrevStrDeal("/*","*/",0,1))
    mgs.add(strz.PrevStrDeal("'''","'''",0,0,1))
    mgs.add(strz.PrevStrDeal('"""','"""',0,0,1))
    mgs.add(strz.PrevStrDeal("#","\n",1,1))
    mgs.add(strz.PrevStrDeal("//","\n",1,1))
    mgs.add(strz.PrevStrDeal("'","'",1,0,1))
    mgs.add(strz.PrevStrDeal('"','"',1,0,1))
    mgs.add(nextz.PrevNextDeal())
    g_mg = mgs
    return mgs

pass
g_mgx = None
g_colon = None
def build_args(as_bytes=False, as_args = False, colon = True):
    global g_mgx,g_colon
    if g_mgx is not None and g_mgx.as_bytes == as_bytes and g_colon == colon:
        return g_mgx
    mgs = mg.Manager(as_bytes)
    if colon:
        mgs.add(setz.SetDeal(':'))
    mgs.add(setz.SetDeal('='))
    mgs.add(spt.PrevSptDeal(",",1))
    mgs.add(spt.PrevSptDeal(';',1))
    mgs.add(spt.PrevSptDeal('\n'))
    mgs.add(spt.PrevSptDeal(' '))
    build_lrval(mgs)
    # mgs.add(listz.ListDeal("(", ")"))
    # mgs.add(listz.ListDeal("[", "]"))
    # mgs.add(mapz.MapDeal("{", "}"))
    mgs.add(listmapz.ListMapDeal("(", ")", as_args=as_args))
    mgs.add(listmapz.ListMapDeal("[", "]", as_args =as_args))
    mgs.add(listmapz.ListMapDeal("{", "}", True, as_args=as_args))
    build_val(mgs)
    #1,0,0,1: 没引号当r"..."
    #1,0,1,1: 没引导当"..."
    mgs.add(strz.PrevStrDeal("r'''","'''",0,0,0))
    mgs.add(strz.PrevStrDeal('r"""','"""',0,0,0))
    mgs.add(strz.PrevStrDeal("r'","'",1,0,0,1))
    mgs.add(strz.PrevStrDeal('r"','"',1,0,0))
    mgs.add(strz.PrevStrDeal("###","###",0,1))
    mgs.add(strz.PrevStrDeal("/*","*/",0,1))
    mgs.add(strz.PrevStrDeal("'''","'''",0,0,1))
    mgs.add(strz.PrevStrDeal('"""','"""',0,0,1))
    mgs.add(strz.PrevStrDeal("#","\n",1,1))
    mgs.add(strz.PrevStrDeal("//","\n",1,1))
    mgs.add(strz.PrevStrDeal("'","'",1,0,1))
    mgs.add(strz.PrevStrDeal('"','"',1,0,1))
    mgs.add(nextz.PrevNextDeal())
    g_colon = colon
    g_mgx = mgs
    return mgs

pass
def load(read, as_bytes = False):
    mgs = build(as_bytes)
    return msg.loads(read)

pass
def is_args(obj):
    return type(obj)==listmapz.Args

pass
def loads_args(s, as_args = False, out_args=False, colon = True):
    mgs = build_args(type(s)==bytes, as_args, colon)
    #input = buffer.BufferInput(s)
    rst = mgs.loads(s)
    if not out_args:
        return rst
    if is_args(rst):
        return rst
    if type(rst) not in [list, dict]:
        rst = [rst]
    if type(rst)==list:
        rst = [rst, {}]
    else:
        rst = [[], rst]
    return listmapz.Args(*rst)

pass
loadx = loads_args
def loads(s):
    mgs = build(type(s)==bytes)
    #input = buffer.BufferInput(s)
    return mgs.loads(s)

pass

def loadf(fp, bts = False, **maps):
    if not os.path.isfile(fp):
        if 'default' in maps:
            return maps['default']
    if bts:
        s = file.bread(fp)
    else:
        s = file.fread(fp)
    return loads(s)

pass
def loadxf(fp, bts = False, **maps):
    if not os.path.isfile(fp):
        if 'default' in maps:
            return maps['default']
    if bts:
        s = file.bread(fp)
    else:
        s = file.fread(fp)
    return loadx(s)

pass