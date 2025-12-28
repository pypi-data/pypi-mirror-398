#

#from buildz.argz import conf_argz as argz
from buildz.argz import conf_callz as callz
from buildz.tls import *
conf = r"""
(
    (argz, main)
    (search, test_ret,test_var,test_env)
)
{
    type: argz
    id: search
    call: search_fc
    judge: eq(args[0], search)
    conf={
        range: 1
        dict: {
            dp: ((0, dp), false, (null,1))
            pt_fp: ((1, pt_fp), (true,null))
            pt: ((2, pt), (true,null))
        }
    }
}
[
    (argz_ret, test_ret)
    [1]
    eq(args[0], test)
]
[
    (argz_env, test_env)
    [1]
    eq(args[0], env)
]
[
    (argz, test_var)
    test_fc
    eq(args(0), var)
]
[
    (cvar, search_fc)
    buildz.fz.search
]
[
    (obj, search_obj)
    buildz.fz.search
    [(ref, dp)]
]
(
    (vargz, vmain)
    (vsearch)
)
(
    (val, test_var),123
)
{
    type: vargz
    id: vsearch
    call: search_obj
    judge: and(eq(args[0], search),eq(ref(test_var),123))
    conf={
        range: 1
        dict: {
            dp: ((0, dp), false, (null,1))
            pt_fp: ((1, pt_fp), (true,null))
            pt: ((2, pt), (true,null))
        }
    }
}
"""
def test_fc(*a, **b):
    print(f"test_fc({a}, {b})")
    return a,b
def test():
    args = ['search','.']
    maps = {
        'pt_fp': r".*\.py$"
    }
    bd = argz.build()
    bd.adds(conf)
    bd.push_var("test_fc",test_fc)
    #rst = bd("main", args, maps)
    rst = bd.get("vmain", args, maps)
    print(f"rst: {rst}")
    print(bd.mg.envs)
    pass

pass

pyz.lc(locals(),test)