from buildz import Base, xf
from . import build
class ArgExp(Exception):
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"stype: {self.stype}, trs: {self.trs}, des: {self.des}"
    def __init__(self, stype, trs, des=None, prev = None):
        super().__init__()
        self.prev = prev
        self.stype = stype
        self.trs = trs
        self.des = des

pass
class Args(Base):
    def call(self, args, maps):
        return args, maps
    def deal_exp(self, exp):
        return exp

pass
class ArrArgs(Args):
    def init(self, args = None):
        if args is None:
            args = []
        self.args = args
    def add(self, item):
        self.args.append(item)
        return self
    def call(self, args, maps):
        i=0
        try:
            for i in range(len(self.args)):
                item = self.args[i]
                args, maps = item(args,maps)
        except ArgExp as exp:
            for j in range(i-1, -1, -1):
                exp = self.args[j].deal_exp(exp)
            raise exp
        return args, maps
    def deal_exp(self, exp):
        for i in range(len(self.args)-1, -1, -1):
            exp = self.args[i].deal_exp(exp)
        return exp
class RangeListArgs(Args):
    def init(self, min = 0, max = None):
        self.min = min
        self.max = max
    def deal_exp(self, exp):
        trs = set()
        for key, vtype in exp.trs:
            if vtype=='list':
                trs.add((key+self.min, vtype))
            else:
                trs.add((key, vtype))
        #exp.trs = trs
        return ArgExp(exp.stype, trs, exp.des, exp)
    def call(self, args, maps):
        if len(args)<self.min:
            raise ArgExp("need", set([(self.min, 'list')]))
        if self.max is None:
            args = args[self.min:]
        else:
            args = args[self.min:self.max]
        return args, maps
class RangeListBuild(build.Build):
    def call(self, conf):
        rg = xf.g(conf, range=None)
        if rg is None:
            return None
        if type(rg)==int:
            rg = [rg, None]
        return RangeListArgs(*rg)
class ArgItem(Base):
    # vtype = 'dict' | 'list'
    def init(self, key, vtype="dict", need = False, default = False, value = None, des = None,remove=True):
        self.vtype = vtype
        self.key = key
        self.need = need
        self.default = default
        self.value = value
        self.trs = []
        self.remove = remove
        if des is None:
            des = key
        self.des = des
    def add(self, key, vtype="dict"):
        self.trs.append((key, vtype))
        return self
    def deal_exp(self, exp):
        trs = set()
        for key, vtype in exp.trs:
            if key == self.key and vtype==self.vtype:
                trs.update(self.trs)
            else:
                trs.add((key, vtype))
        #exp.trs = trs
        return ArgExp(exp.stype, trs, exp.des, exp)
        return exp
    def call(self, set_args, args, maps, rst_args, rst_maps):
        val = None
        find = False
        for key, vtype in self.trs:
            if vtype =="dict":
                if xf.dhas(maps, key):
                    val = xf.dget(maps, key)
                    if self.remove:
                        xf.dremove(maps, key)
                    find=True
                    break
                #if key in maps:
                #    val = maps[key]
                #    if self.remove:
                #        del maps[key]
                #    find = True
                #    break
            else:
                if key in set_args:
                    val = args[key]
                    if self.remove:
                        set_args.remove(key)
                    find = True
                    break
        if not find:
            if self.default:
                find = True
                val = self.value
        if not find and self.need:
            raise ArgExp("need", set(self.trs), self.des)
        if self.vtype == 'dict':
            xf.dset(rst_maps, self.key, val)
            #rst_maps[self.key] = val
        else:
            rst_args[self.key] = val

pass
class ArgItemBuild(build.Build):
    def call(self, key, vtype, conf):
        need = xf.g(conf, need=False)
        default = xf.g(conf, default=False)
        value = xf.g(conf, value=None)
        des = xf.g(conf, des=None)
        remove = xf.g(conf, remove=True)
        src = xf.g(conf, src=None)
        srcs = xf.g(conf, srcs = [])
        if src is not None:
            srcs.append(src)
        src = srcs
        item = ArgItem(key, vtype, need, default, value, des, remove)
        for s in src:
            if type(s) not in (list, tuple):
                if type(s)==int:
                    s = [s, 'list']
                else:
                    s = [s, 'dict']
            if s[1] in ('l', 'args'):
                s[1] = 'list'
            elif s[1] in ('d', 'maps'):
                s[1] = 'dict'
            item.add(*s)
        return item
class TrsArgs(Args):
    def deal_exp(self, exp):
        for item in self.args:
            exp = item.deal_exp(exp)
        return exp
    def init(self, args=None, keep = True):
        super().init()
        if args is None:
            args = []
        self.args = args
        self.keep = keep
    def add(self, item):
        self.args.append(item)
        return self
    def call(self, args, maps):
        rst_args, rst_maps = {}, {}
        set_args = set(range(len(args)))
        for item in self.args:
            item(set_args, args, maps, rst_args, rst_maps)
        l_args = 0
        if len(rst_args)>0:
            l_args= max(rst_args.keys())
        out_args = []
        if self.keep and len(set_args)>0:
            for i in range(max(set_args)):
                if i in set_args:
                    out_args.append(args[i])
        for i in range(l_args+1):
            if i in rst_args:
                if len(out_args)<i:
                    raise ArgExp("need", set([(i, 'list')]))
                out_args.append(rst_args[i])
        if self.keep:
            for k in maps:
                if k not in rst_maps:
                    rst_maps[k] = maps[k]
        return out_args, rst_maps

pass
class TrsArgsBuild(build.Build):
    def init(self):
        self.item = ArgItemBuild()
        super().init(self.item)
    def call(self, conf):
        keep = xf.g(conf, keep = False)
        lst = xf.g1(conf, list={}, args={})
        dct = xf.g1(conf, dict={}, maps={})
        items = []
        for k, val in lst.items():
            items.append(self.item(k, 'list', val))
        for k, val in dct.items():
            items.append(self.item(k, 'dict', val))
        if len(items)==0:
            return None
        return TrsArgs(items, keep)
class ArrArgsBuild(build.Build):
    def init(self):
        self.range = RangeListBuild()
        self.trs = TrsArgsBuild()
        super().init(self.trs, self.range)
    def call(self, conf):
        rg = self.range(conf)
        trs = self.trs(conf)
        if rg is None and trs is None:
            return None
        arr = [rg, trs]
        arr = [k for k in arr if k is not None]
        if len(arr)==1:
            return arr[0]
        return ArrArgs(arr)
