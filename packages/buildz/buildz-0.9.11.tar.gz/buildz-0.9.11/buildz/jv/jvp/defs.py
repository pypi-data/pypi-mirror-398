#
import re
from .jsc import fetch_method_text, rps_dct, fetch_vals,fetch_vars
from .util import make_fcs
sc_def = r'''
    <type> <method>(<params>) <exp>{
        <ret><call>(<args>);
    }
'''.rstrip()
#def default(codes, args, text):
def default(_type, method, params, exp, args):
    #_type, method, params, has_def = fetch_method_text(codes, text)
    rst = []
    if args is None or args.strip()=='':
        return rst, []
    arr = fetch_vals(args)
    call = method
    ret = 'return '
    if _type.strip() in ['','public','protected','private']:
        call = "this"
        ret = ''
    if _type.find("void")>=0:
        ret = ""
    params = [k.strip() for k in fetch_vars(params)]
    vars = [k.split(" ")[-1] for k in params]
    for i in range(1, len(arr)+1):
        defs = arr[-i:]
        _params = params[:-i]
        _vs = vars[:-i]
        _vs = _vs+defs
        _vs = ", ".join(_vs)
        _params = ", ".join(_params)
        s = rps_dct(sc_def, type=_type, method = method, params=_params, ret = ret, call=call, args = _vs, exp=exp)
        rst.append(s)
    return rst, []
defaults = make_fcs(default,True)