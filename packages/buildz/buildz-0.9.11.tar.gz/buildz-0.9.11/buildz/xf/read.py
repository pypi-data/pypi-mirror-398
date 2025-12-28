
from .loader import mg, buffer, base

from .loader.deal import nextz, spt, strz, listz, spc, setz, mapz, reval, lrval
def bl(val):
    trues = [base.BaseDeal.like(k, val) for k in ["true", "True", "1"]]
    trues += [1,True]
    falses = [base.BaseDeal.like(k, val) for k in ["false", "False", "0"]]
    falses += [0,False]
    if val in trues:
        return True
    elif val in falses:
        return False
    else:
        raise Exception("unknown bool val")

pass
def build_lrval(mgs):
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
    mgs.add(reval.ValDeal("[\+\-]?\d+e[\+\-]?\d+", float))
    mgs.add(reval.ValDeal("null", lambda x:None))
    mgs.add(reval.ValDeal("true", lambda x:True))
    mgs.add(reval.ValDeal("false", lambda x:False))

pass
def build():
    mgs = mg.Manager()
    mgs.add(spc.PrevSpcDeal())
    build_val(mgs)
    mgs.add(strz.PrevStrDeal("r'''","'''",0,0,0))
    mgs.add(strz.PrevStrDeal('r"""','"""',0,0,0))
    mgs.add(strz.PrevStrDeal("r'","'",1,0,0))
    mgs.add(strz.PrevStrDeal('r"','"',1,0,0))
    mgs.add(strz.PrevStrDeal("###","###",0,1))
    mgs.add(strz.PrevStrDeal("/*","*/",0,1))
    mgs.add(strz.PrevStrDeal("'''","'''",0,0,1))
    mgs.add(strz.PrevStrDeal('"""','"""',0,0,1))
    mgs.add(strz.PrevStrDeal("#","\n",1,1))
    mgs.add(strz.PrevStrDeal("//","\n",1,1))
    mgs.add(strz.PrevStrDeal("'","'",1,0,1))
    mgs.add(strz.PrevStrDeal('"','"',1,0,1))
    mgs.add(setz.SetDeal(':'))
    mgs.add(setz.SetDeal('='))
    mgs.add(spt.PrevSptDeal(',',1))
    mgs.add(spt.PrevSptDeal(';',1))
    mgs.add(spt.PrevSptDeal('\n'))
    build_lrval(mgs)
    mgs.add(listz.ListDeal("(", ")"))
    mgs.add(listz.ListDeal("[", "]"))
    mgs.add(mapz.MapDeal("{", "}"))
    mgs.add(nextz.PrevNextDeal())
    return mgs

pass
def load(read):
    mgs = build()
    return msg.load(read)
def loads(s):
    # lr = "{}"
    # ls = "{[("
    # if type(s)==bytes:
    #     lr = lr.encode()
    #     ls = ls.encode()
    # x = s.strip()
    # if len(x)>0 and x[0] not in ls:
    #     s = lr[0]+s+lr[1]
    mgs = build()
    input = buffer.BufferInput(s)
    return mgs.load(s)

pass
