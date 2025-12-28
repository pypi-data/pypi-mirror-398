#

import re
from .jsc import fetch_methods_text, rps_dct, fetch_vals, fetch_vars
from .util import make_fcs
from buildz import argx, xf, dz
'''
public type abc(key, ...){
    ...
}
add:
public type fcs(String keys, Object[] vals, ...) {

}
'''
sc_vals = '''
if (i<vals.length) {
                <get_val><call>(ks[i], vals[i]<others>);
            } else {
                <get_val><call>(ks[i]<null_default><others>);
            }
'''.strip()
sc_nval = '''
<get_val><call>(ks[i]<others>);
'''.strip()
sc_fcs = """
    <type> <method>(<params>)<exp> {
        String[] ks = sptsKeys(keys);
        <align><def_rst>
        for (int i=0;i<ks.length;i++) {
            <def_val>
            <call>
            <add_val>
        }
        <ret_rst>
    }
""".rstrip()
'''
methods(method_name, val, ret, align, null_default)
'''
def _fcs(_type, method, params, exp, args):
    rst = []
    args = xf.loadx(args, out_args=True, as_args=False)
    lst,maps = args.lists, args.dicts
    fetch = argx.Fetch(*xf.loads(r"[method,val, ret,align,default],{}"))
    conf = fetch.fetch(lst, maps)
    wmethod, has_val,ret, align, default = dz.g(conf, method=0, val=None, ret=None,align=True,default='null')

    params = [k.strip() for k in fetch_vars(params)]
    if len(params)==1:
        has_val = False
    if has_val:
        param = params[1]
        val_type = ' '.join(param.split(" ")[:-1])
    else:
        val_type = None
        align = False
    vars = [k.split(" ")[-1].strip() for k in params]
    if len(params)==1:
        val_type = None
        align = False
    unit_type = _type.replace("public","").replace("private","").replace("protected","").replace("static","").strip()
    if ret is None:
        ret = unit_type not in ('void','')
    check_align = ''
    if align:
        assert val_type is not None, f"_fcs({_type}, {method}, {params}, {args})"
        check_align = 'if(ks.length>vals.length)throw new RuntimeException("not enough vals");'
    if (val_type is not None):
        outs_params = ["String keys", f"{val_type}[] vals"]+params[2:]
        others = vars[2:]
        sc_v = sc_vals
    else:
        sc_v = sc_nval
        outs_params = ["String keys"]+params[1:]
        others = vars[1:]
    if len(others)==0:
        others = ""
    else:
        others = ", ".join(others)
        others = ", "+others
    outs_params = ", ".join(outs_params)
    null_default = ""
    if default is not None:
        null_default = f", {default}"
    out_type = "public void"
    def_rst, ret_rst, def_val, get_val, add_val = "","","","",""
    if ret:
        out_type = f"public {unit_type}[]" 
        def_rst = f"{unit_type}[] rst = new {unit_type}[ks.length];" 
        ret_rst = "return rst;"
        def_val = f"{unit_type} val;"
        get_val = "val="
        add_val = "rst[i] = val;"
    sc_v = rps_dct(sc_v, get_val=get_val, call=method, others = others, null_default = null_default)
    s = rps_dct(sc_fcs, type=out_type, method = wmethod, params = outs_params, align = check_align, def_rst = def_rst, def_val = def_val, call = sc_v, add_val = add_val, ret_rst = ret_rst, exp=exp)
    return [s], []
fcs = make_fcs(_fcs, False)
