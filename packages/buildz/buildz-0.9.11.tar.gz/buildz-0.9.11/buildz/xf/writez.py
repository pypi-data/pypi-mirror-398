
from .writerz import mg, itemz, base, conf
from .writerz.deal import listz, mapz, strz, reval, jsonval, listmapz
from . import file
from decimal import Decimal
from .base import Args
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
        mgs.add([bytes, str], strz.StrDeal('"','"', pts))
        mgs.add(float, reval.ValDeal(lambda x:str(x)))
        mgs.add(int, reval.ValDeal(lambda x:str(x)))
        mgs.add(type(None), reval.ValDeal(lambda x:'null'))
        mgs.add(Decimal, reval.ValDeal(lambda x:str(x)))
        mgs.add(bool, reval.ValDeal(lambda x:'true' if x else 'false'))
    else:
        mgs.add([bytes, str, float, int, type(None), Decimal, bool], jsonval.ValDeal())
    mgs.add([list, tuple, set], listz.ListDeal('[',']',','))
    mgs.add(dict, mapz.MapDeal('{','}',':',','))
    if args:
        mgs.add(Args, listmapz.ListMapDeal('(',')','=',','))
    return mgs

pass
def dumps(obj, bytes = 0, format = 0, not_format_height = 1, json_format= 0, args = False, deep=None):
    if deep is not None:
        not_format_height = deep+1
    cf = conf.Conf()
    cf.set(bytes=bytes, format=format, nfmt_height=not_format_height)
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

def dumpf(obj, filepath, bytes = 0, format = 0, not_format_height = 1, json_format= 0, mode = 'wb', args = False, deep=None):
    if deep is not None:
        not_format_height = deep+1
    s = dumps(obj, bytes = bytes, format = format, not_format_height = not_format_height, json_format= json_format).encode("utf-8")
    file.fwrite(s, filepath, mode)

pass
def dumpxf(*a, **b):
    return dumpf(*a, **b, args=True)

pass

def dump(output, obj, *argv, **maps):
    rs = dumps(obj, *argv, **maps)
    output(rs)

pass
