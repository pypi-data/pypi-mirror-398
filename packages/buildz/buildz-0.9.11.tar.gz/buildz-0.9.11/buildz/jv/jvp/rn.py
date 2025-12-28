#

import re
from .jsc import fetch_methods_text, rps_dct, fetch_vals,fetch_vars

from .util import make_fcs
sc_rename = """
    <type> <method>(<params>)<exp> {
        <ret><call>(<vars>);
    }
""".rstrip()
# def rename(codes, args, text):
#     _type, method, params, has_def = fetch_method_text(codes, text)
#     rst = []
#     if has_def:
#         rst.append(codes.rstrip())
def rename(_type, method, params, exp, args):
    rst = []
    args = fetch_vals(args)
    ret = "return " if _type.find("void")<0 else ""
    wmethod = args[0]
    params = [k.strip() for k in fetch_vars(params)]
    vars = [k.split(" ")[-1].strip() for k in params]
    key = 'key'
    if len(args)>1:
        key =args[1]
    rs = rps_dct(sc_rename, type =_type,method=wmethod,params=', '.join(params), call=method, vars = ', '.join(vars), ret = ret,exp=exp)
    rst.append(rs)
    rst.reverse()
    return rst, []
    
renames = make_fcs(rename, False)
