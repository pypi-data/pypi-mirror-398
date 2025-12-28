from .dz import Conf
from . import xf, pathz, pyz, argx, dz
import sys, os
def load_conf(conf, dp=None, dp_key = 'dp', src_key = 'src.conf'):
    if type(conf)==dict:
        conf = Conf().update(conf)
    fps, base = conf.gets('fps, conf', [], {})
    if type(fps)==str:
        fps = [fps]
    conf_first,replace,flush,visit_list = conf.gets('conf_first,replace,flush,visit_list',1, 1,1,0)
    spt, spts = conf.gets('spt, spts','.',',')
    dp = conf.get(dp_key, dp)
    conf.set(dp_key, dp)
    path = pathz.Path()
    path.set("dp", dp)
    rst = Conf(spt, spts)
    if src_key is not None:
        rst.set(src_key, conf)
    if conf_first:
        rst.update(base, flush, replace, visit_list)
    for fp in fps:
        tmp = xf.loadf(path.dp(fp))
        if type(tmp)!=dict:
            continue
        rst.update(tmp, flush, replace, visit_list)
    if not conf_first:
        rst.update(base, flush, replace, visit_list)
    return rst
# using
def calls(conf):
    calls = conf.get("calls", [])
    local = conf.get("local", False)
    root = conf.top()
    if type(calls)==dict:
        target = dz.g(calls, target='run')
        calls = dz.get(calls, target, [])
        # if target in calls:
        #     calls = dz.get(calls, target, [])
        # else:
        #     calls = root.get(target, [])
    if type(calls)==dict:
        dm, init, calls, init_cover = dz.g(calls, domain=None, init = {},calls=[], init_cover=False)
        if len(init)>0:
            init_conf = conf.top("confz.init")
            if dm is not None:
                init_conf = init_conf(dm)
            init_conf.update(init, replace=init_cover)
            root.update(init_conf.val())
    if type(calls)==str:
        calls = [calls]
    obj = conf
    if not local:
        obj = root
    for key in calls:
        #assert obj.has(key), f"not has key: '{key}'"
        simple(obj.l(key))
    return conf
fn_key = "confz.fns"
fn_cache_key = "confz.fn.caches"
default_fn_key = "confz.fn.default"
def fn2fc(conf, key = 'fn', default_fn = None, default_fc = None):
    fn = conf.get(key)
    conf = conf()
    if fn is None:
        if default_fc is not None:
            return default_fc
        fn = default_fn or conf.get(default_fn_key, 'calls')
    fc = conf(fn_cache_key).get(fn)
    if fc is not None:
        return fc
    path =conf(fn_key).get(fn)
    if path is None:
        return None
    fc = pyz.load(path)
    conf(fn_cache_key).set(fn,fc)
    return fc
def get_fc(conf, fc_key='fc', fn_key='fn', default_fn = None, default_fc = None):
    fc = conf.get(fc_key)
    if fc is None:
        fc = fn2fc(conf, fn_key, default_fn, default_fc)
    else:
        fc = pyz.load(fc)
    return fc
def conf_update(conf):
    if conf.get_type()==str:
        conf = conf.ltop(conf.domain)
    up = conf.get('up', link=0)
    return conf
def deep_link(conf):
    up = conf.get('up', link=0)
    if not up:
        return
    deep_link(conf.top(up))
    conf().link(conf.domain, up)
    #conf.remove('up')
def deep_copy(conf):
    src = conf.get('copy', link=0)
    if not src:
        return
    deep_copy(conf.top(src))
    conf.update(conf.top(src).val(),replace=0)
    #conf.remove('copy')
def simple(conf):
    if conf.get_type()==str:
        conf = conf.ltop(conf.domain)
    deep_link(conf)
    deep_copy(conf)
    fc = get_fc(conf, default_fn = "calls")
    if fc == calls and not conf.has("calls"):
        fc = None
    if fc is None :
        fc = pyz.load(conf.domain)
    assert fc is not None, f"conf has not setted deal fc: {conf}"
    return fc(conf)
def get_sys_conf(conf = []):
    if type(conf) == str:
        conf = xf.loadf(conf)
    if conf is None:
        conf = []
    fetch = argx.Fetch(*conf)
    return fetch()
def fc_set(conf):
    """
        fn: set
        // domain: default=None
        // replace: default=1
        // flush: default=1
        conf: {

        }
    """
    maps,domain,flush,replace = conf.gets("conf, domain,flush,replace",None,None,1,1)
    if maps is None:
        return conf
    conf.top(domain).update(maps, flush=flush, replace=replace)
    return conf
def judge_fc(conf):
    fc = get_fc(conf, "judge_fc", "judge")
    rst = fc(conf)
    if rst:
        if not conf.has("yes"):
            return None
        conf = conf.l("yes")
    else:
        if not conf.has("no"):
            return None
        conf = conf.l("no")
    return simple(conf)
def switch_fc(conf):
    fc = get_fc(conf, "cal_fc", "cal", "get")
    val = fc(conf)
    deal_conf = conf("vals")(val)
    deal = get_fc(conf, "deal_fc", "deal", "mset")
    return deal(deal_conf)
def sub_conf(conf):
    deal = get_fc(conf, "deal_fc", "deal", "mset")
    val = conf("val")
    return deal(val)
def msets(conf, keys = []):
    # if not conf.has_val():
    #     return conf
    for k,v in conf.val().items():
        ks = keys+[k]
        if type(v)==str:
            val = conf.top(v).val()
            conf().set(conf.key(ks), val)
            #conf().top(conf.key(ks)).update(val)
            pass
        else:
            msets(conf(k), ks)
            #conf().top(k).update(v)
    return conf
def init_fn(conf):
    maps = {
        "calls": calls,
        "set": fc_set,
        "judge": judge_fc,
        "switch": switch_fc,
        "has_set": lambda conf:conf.top().has(conf.get("key")),
        "equal": lambda conf:conf.top().get(conf.get("key"))==conf.get("val"),
        "get": lambda conf: conf.top().get(conf.get("key")),
        "mset": lambda conf:conf.top().update(conf.val()) if conf.has_val() else conf,
        "deal_val":sub_conf,
        "msets": msets
    }
    conf(fn_cache_key).update(maps, replace=False)
def run(dp = None, fp = None, init_conf = {}):
    if dp is None:
        dp = os.path.dirname(__file__)
    path = pathz.Path()
    path.set('dp', dp)
    conf = {}
    if fp is not None:
        conf = xf.loadf(path.dp(fp))
    #sys_conf = get_sys_conf()
    xf.fill(init_conf, conf, 1)
    conf = Conf().update(conf)
    init = conf.get(conf.get("key.init", "init"), {})
    conf = load_conf(conf, dp).update(init)
    conf.set("confz.init", init)
    init_fn(conf)
    return simple(conf)
    #return conf
def test():
    run()
pyz.lc(locals(), test)