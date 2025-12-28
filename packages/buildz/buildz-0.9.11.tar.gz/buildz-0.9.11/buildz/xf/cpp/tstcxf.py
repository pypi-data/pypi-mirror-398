#
# set PYTHONVERBOSE=1
import pcxf
def build_str(bts):
    return bts.decode("utf-8")
def deal_exp(s):
    print(s)

pass
def test():
    import time
    n_list =1500
    n_dict=500
    n=3
    #n_arr = 10
    obj = [1,2,3]
    rst = []
    for i in range(n_list):
        rst.append(obj)
    obj = rst
    rst = {}
    for j in range(n_dict):
        rst[j] = obj
    obj = rst
    import json
    from buildz import xf
    from buildz.xf import readz_nexp
    s = json.dumps(obj)
    bs = s.encode("utf-8")
    print("start")
    for i in range(n):
        curr=time.time()
        jobj = json.loads(s)
        sec = time.time()-curr
        print(f"json loads: {sec}, {type(jobj)}")
    print(f"xf.loads:", xf.loads)
    for i in range(n):
        curr=time.time()
        rst = xf.loads(bs)
        sec = time.time()-curr
        print("xf rst:", type(rst), "sec:", sec)
    # print(f"readz_nexp.loads:", readz_nexp.loads)
    # for i in range(n):
    #     curr=time.time()
    #     rst = readz_nexp.loads(bs)
    #     sec = time.time()-curr
    #     print("readz_nexp rst:", type(rst), "sec:", sec)
    for i in range(n):
        curr=time.time()
        tst_obj = pcxf.loads(bs)
        sec = time.time()-curr
        print(f"pcxf loads: {sec}, {type(tst_obj)}, {tst_obj==jobj}")
rst = pcxf.loads(b"{1={1=2,3=4,'123'=(1,2,3)},3=4,'5'=[1,2,3]}")
#rst = pcxf.py_loads("{}", build_str, deal_exp)
print("rst:",rst)
test()

