
from .writer import mg, itemz, base, conf
from .writer.deal import listz, mapz, strz, reval, jsonval, listmapz
from . import file
from decimal import Decimal
pts = [
    "[\+\-]?\d+",
    "[\+\-]?\d+\.\d+",
    "[\+\-]?\d+e[\+\-]?\d+",
    "null",
    "true",
    "false",
    "[\s\S]*[\n\r\t\:\[\]\{\}\(\)\,\:\=\'\<\>\" \|\#\;\/][\s\S]*"
]
def build(json_format=False, args = False):
    mgs = mg.Manager()
    if not json_format:
        mgs.add(strz.StrDeal('"','"', pts))
        mgs.add(reval.ValDeal(float, lambda x:str(x)))
        mgs.add(reval.ValDeal(int, lambda x:str(x)))
        mgs.add(reval.ValDeal(type(None), lambda x:'null'))
        mgs.add(reval.ValDeal(Decimal, lambda x:str(x)))
        mgs.add(reval.ValDeal(bool, lambda x:'true' if x else 'false'))
    else:
        mgs.add(jsonval.ValDeal())
    mgs.add(listz.ListDeal('[',']',','))
    mgs.add(mapz.MapDeal('{','}',':',','))
    if args:
        mgs.add(listmapz.ListMapDeal('{','}',':',','))
    return mgs

pass
def dumps(obj, bytes = 0, format = 0, deep = 0, json_format= 0, args = False):
    cf = conf.Conf()
    cf.set(bytes=bytes, format=format, deep=deep)
    if format:
        cf.set(set=1, prev=1,line=4, spc=' ')
    else:
        cf.set(set=1, prev=1)
    mgs = build(json_format, args)
    return mgs.dump(obj, cf)

pass
def dumpx(*a, **b):
    return dumps(*a, **b, args=True)

pass

def dumpf(obj, filepath, bytes = 0, format = 0, deep = 0, json_format= 0, mode = 'wb', args = False):
    s = dumps(obj, bytes = bytes, format = format, deep = deep, json_format= json_format).encode("utf-8")
    file.fwrite(s, filepath, mode)

pass
def dumpxf(*a, **b):
    return dumpf(*a, **b, args=True)

pass

def dump(output, obj, *argv, **maps):
    rs = dumps(obj, *argv, **maps)
    output(rs)

pass
