#coding=utf-8
import sys,re
from .base import Base
class Fetch:
    """
    命令行参数读取
    ft = Fetch("id,name,kind".split(","), {"a":"age"})
        or
    ft = Fetch(*xf.loads("[[id,name,kind],{a:age}]"))

    ft("001 zero life -a12".split(" ")) = {'id': '001', 'name': 'zero', 'kind': 'life', 'age': '12'}

    但更简单的方法是:
    xf.args("{id:'001', name: zero, kind: life, age: 12}".split(" ")) = {'id': '001', 'name': 'zero', 'kind': 'life', 'age': 12}
    python buildz.xf {id:'001', name: zero, kind: life, age: 12}
    就是对引号不太适用
    """
    def __init__(self, args = [], maps ={}):
        args = [maps[k] if k in maps else k for k in args]
        self.args = args
        self.maps = maps
    def des(self):
        cmd = " ".join(self.args)
        adds = []
        for k, val in self.maps.items():
            tmp = f"    [-{k} param] [--{val}=param]"
            adds.append(tmp)
        adds = [cmd]+adds
        rs = "\n".join(adds)
        return rs
    def check(self, args, ks):
        rst = []
        for k in ks:
            if k not in args:
                rst.append(k)
        return rst
    def __call__(self, argv = None):
        args, maps = fetch(argv)
        return self.fetch(args, maps)
    def fetch(self, args, maps):
        rst = {}
        for i in range(len(args)):
            if i >= len(self.args):
                break
            key = self.args[i]
            rst[key] = args[i]
        for key in maps:
            rst[key] = maps[key]
        keys = list(rst.keys())
        while len(keys)>0:
            key = keys.pop(0)
            if key in self.maps:
                rkeys = self.maps[key]
                if type(rkeys) not in (list, tuple):
                    rkeys = [rkeys]
                for rkey in rkeys:
                    assert rkey!=key, f'error rkey==key: {key}'
                    val = rst[key]
                    if rkey not in rst:
                        rst[rkey] = val
                    else:
                        tmp = rst[rkey]
                        if type(tmp)!=list:
                            tmp = [tmp]
                            rst[rkey] = tmp
                        tmp.append(val)
                    keys.append(rkey)
                    keys = list(set(keys))
                del rst[key]
        # for key in keys:
        #     while key in self.maps:
        #         rkeys = self.maps[key]
        #         if type(rkeys) not in (list, tuple):
        #             rkeys = [rkeys]
        #         for rkey in rkeys:
        #             if key in rst:
        #                 val = rst[key]
        #                 rst[rkey] = val
        #                 del rst[key]
        #         key = rkey
        return rst

pass
class FetchX(Fetch):
    def __init__(self, *a, **b):
        super().__init__(a,b)

pass

def build_pt(pt, fc):
    st = "^"
    ed = "$"
    if pt[0]!=st:
        pt = st+pt
    if pt[-1]!=ed:
        pt = pt+ed
    def wfc(val):
        if re.match(pt, val) is None:
            return None, 0
        val = fc(val)
        return val, 1
    return wfc

pass
class ValDeals(Base):
    def init(self):
        self.deals = []
    def add(self, fc):
        self.deals.append(fc)
    def call(self, val):
        if type(val)!=str:
            return val
        for deal in self.deals:
            rst, done = deal(val)
            if done:
                return rst
        return val

pass
to_val = ValDeals()
to_val.add(build_pt("[\+\-]?\d+", int))
to_val.add(build_pt("[\+\-]?\d*\.\d+", float))
to_val.add(build_pt("[\+\-]?\d*(?:\.\d+)?e[\+\-]?\d+", float))
to_val.add(build_pt("null", lambda x:None))
to_val.add(build_pt("true", lambda x:True))
to_val.add(build_pt("false", lambda x:False))

def fetch(argv = None):
    r"""
    format: a b c -a 123 -b456 --c=789 +d  -x"??? ???" y z
    return: [a,b,c,y,z], {a:123,b:456,c:789,d:1,x:'??? ???'}
    """
    if argv is None:
        argv = sys.argv[1:]
    lists, maps = [],{}
    argv = [str(k).strip() for k in argv]
    argv = [k for k in argv if k!=""]
    i = 0
    while i<len(argv):
        v = argv[i]
        make_plus = 0
        if v in ["-", "--", "+"]or v[0] not in "+-":
            v = to_val(v)
            lists.append(v)
            i+=1
            continue
        if v[0] == "+":
            key = v[1:]
            make_plus = 1
            val = 1
        else:
            if v[1]=="-":
                kv = v[2:]
                x = kv.split("=")
                key = x[0]
                val = "=".join(x[1:])
                if len(val)==0:
                    val = 1
            else:
                key = v[1]
                if len(v)>2:
                    val = v[2:]
                else:
                    if i+1>=len(argv):
                        val = 1
                    else:
                        val = argv[i+1]
                        i+=1
        if make_plus:
            keys = key.split(",")
        else:
            keys = [key]
        for key in keys:
            if key not in maps:
                maps[key] = []
            val = to_val(val)
            maps[key].append(val)
        i+=1
    for k in maps:
        v = maps[k]
        if len(v)==1:
            maps[k] = v[0]
    return lists, maps

pass

def get(maps, keys, default=None):
    if type(keys) not in [list, tuple]:
        keys = [keys]
    for key in keys:
        if key in maps:
            return maps[key]
    return default

pass
        

