#

import re
from .jsc import fetch_methods_text, rps_dct, fetch_vals,fetch_vars
from .util import make_fcs

sc_dm = """
    <type> <method>(<params>) <exp>{
        <key> = dmKey(<key>);
        Conf obj = this;
        if (root != null) {
            obj = root;
        }
        <ret>obj.<call>(<vars>);
    }
""".rstrip()
# def domains(codes, args, text):
#     fcs, has_def = fetch_methods_text(codes, text)
#     rst = []
#     if has_def:
#         rst.append(codes.rstrip())
#     for _type, method, params in fcs:
#         rst+=domain(_type, method, params, args)
#     return rst
def domain(_type, method, params, exp, args):
    rst = []
    args = fetch_vals(args)
    ret = "return " if _type.find("void")<0 else ""
    if len(args)==0:
        wmethod = method[1:]
    else:
        wmethod = args[0]
    params = [k.strip() for k in fetch_vars(params)]
    vars = [k.split(" ")[-1].strip() for k in params]
    # key = 'key'
    # if len(args)>1:
    #     key =args[1]
    key = vars[0]
    rs = rps_dct(sc_dm, type =_type,method=wmethod,params=', '.join(params), key=key, call=method, vars = ', '.join(vars), ret = ret, exp=exp)
    rst.append(rs)
    #rst.reverse()
    return rst, []
domains = make_fcs(domain,False)
