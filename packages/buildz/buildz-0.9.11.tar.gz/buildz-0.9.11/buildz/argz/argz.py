from .. import Base, xf, dz
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
class ArgType:
    list = 'list'
    dict='dict'
    @staticmethod
    def stand(s):
        if ArgType.islist(s):
            return ArgType.list
        return ArgType.dict
    @staticmethod
    def islist(s):
        return s in ('list','l','lst','args')
    @staticmethod
    def isdict(s):
        return s in ('dict', 'd', 'dct', 'maps')

pass
class Params(Base):
    def str(self):
        return f"Params(args={self.args}, maps={self.maps})"
    def init(self, args=[], maps={}):
        self.args = args
        self.maps = maps
class Args(Base):
    '''
        参数映射基础类
    '''
    Type=ArgType
    def call(self, params):
        return params
    def deal(self, args, maps):
        params = self.call(Params(args,maps))
        return params.args, params.maps
    def deal_exp(self, exp):
        return exp

pass
class ArrArgs(Args):
    '''
        参数映射类的队列，顺序处理
    '''
    def str(self):
        return f"ArrArgs(args={self.args})"
    def init(self, args = None):
        if args is None:
            args = []
        self.args = args
    def add(self, item):
        self.args.append(item)
        return self
    def call(self, params):
        args, maps = params.args, params.maps
        i=0
        try:
            for i in range(len(self.args)):
                item = self.args[i]
                params = item(params)
        except ArgExp as exp:
            exp = self.deal_exp(exp, i-1)
            raise exp
        #params.args, params.maps = args, maps
        return params
    def deal_exp(self, exp, base=None):
        if base is None:
            base = len(self.args)-1
        for i in range(base, -1, -1):
            exp = self.args[i].deal_exp(exp)
        return exp
class RangeListArgs(Args):
    '''
        范围映射
    '''
    def str(self):
        return f"RangeArgs(base={self.base}, last={self.last}, min={self.min})"
    def init(self, base = 0, last = None, min=0):
        self.base = base
        self.last = last
        self.min = min
    def deal_exp(self, exp):
        trs = set()
        for key, vtype in exp.trs:
            if ArgType.islist(vtype):
                trs.add((key+self.base, vtype))
            else:
                trs.add((key, vtype))
        return ArgExp(exp.stype, trs, exp.des, exp)
    def call(self, params):
        args, maps = params.args, params.maps
        if self.last is None:
            args = args[self.base:]
        else:
            args = args[self.base:self.last]
        if len(args)<self.min:
            raise ArgExp("need", set([(self.base, 'list')]))
        return Params(args, maps)
        params.args, params.maps = args, maps
        return params


class ArgItem(Base):
    '''
        单个字段映射处理
    '''
    # vtype = 'dict' | 'list'
    def init(self, key, vtype=ArgType.dict, need = False, default = False, default_value = None, des = None,remove=True):
        self.vtype = vtype
        self.key = key
        self.need = need
        self.default = default
        self.default_value = default_value
        self.trs = []
        self.remove = remove
        if des is None:
            des = key
        self.des = des
    def add(self, key, vtype=ArgType.dict):
        self.trs.append((key, vtype))
        return self
    def deal_exp(self, exp):
        trs = set()
        for key, vtype in exp.trs:
            if key == self.key and vtype==self.vtype:
                trs.update(self.trs)
            else:
                trs.add((key, vtype))
        return ArgExp(exp.stype, trs, exp.des, exp)
    def fetch(self, key, vtype, set_args, args, maps):
        find = False
        val=None
        if ArgType.isdict(vtype):
            val,find = dz.dget(maps, key)
            if find:
                if self.remove:
                    dz.dremove(maps, key)
        else:
            if key in set_args:
                val = args[key]
                if self.remove:
                    set_args.remove(key)
                find = True
        return val, find
    def call(self, set_args, args, maps, rst_args, rst_maps):
        val = None
        find = False
        for key, vtype in self.trs:
            val, find = self.fetch(key, vtype, set_args, args, maps)
            if find:
                break
        if not find and self.default:
            find = True
            val = self.default_value
        if not find and self.need:
            raise ArgExp("need", set(self.trs), self.des)
        if not find:
            return
        if ArgType.isdict(self.vtype):
            xf.dset(rst_maps, self.key, val)
        else:
            rst_args[self.key] = val

pass
class ListFill:
    '''
        数组映射后，中间缺失位置如何处理
        exp=报错
        null=填充None
    '''
    exp='exp'
    null = 'null'
    default=exp
class TrsArgs(Args):
    def str(self):
        return f"TrsArgs(args={len(self.args)}, keep={self.keep}, fill = {self.list_fill})"
    '''
        数据映射
    '''
    def deal_exp(self, exp):
        for item in self.args:
            exp = item.deal_exp(exp)
        return exp
    def init(self, args=None, keep = False, list_fill = ListFill.default):
        super().init()
        if args is None:
            args = []
        self.args = args
        self.keep = keep
        self.list_fill = list_fill
    def add(self, item):
        self.args.append(item)
        return self
    def call(self, params):
        args, maps = params.args, params.maps
        rst_args, rst_maps = {}, {}
        set_args = set(range(len(args)))
        for item in self.args:
            item(set_args, args, maps, rst_args, rst_maps)
        if self.keep and len(set_args)>0:
            for i in set_args:
                if i not in rst_args:
                    rst_args[i] = args[i]
        l_args = 0
        if len(rst_args)>0:
            l_args= max(rst_args.keys())+1
        out_args = []
        for i in range(l_args):
            if i in rst_args:
                out_args.append(rst_args[i])
            else:
                if self.list_fill == ListFill.null:
                    out_args.append(None)
                else:
                    raise ArgExp("need", set([(i, ArgType.list)]))
        if self.keep:
            for k in maps:
                if k not in rst_maps:
                    rst_maps[k] = maps[k]
        return Params(out_args, rst_maps)
        params.args, params.maps = out_args, rst_maps
        return params

pass