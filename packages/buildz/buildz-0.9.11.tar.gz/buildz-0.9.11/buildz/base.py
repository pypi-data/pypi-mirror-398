#coding=utf-8
from . import pyz
def fc_s2l(s):
    if type(s)!=str:
        return s
    arr = s.split(",")
    arr = [k.strip() for k in arr]
    return arr
def fcBase(cls, lst=0, keys = tuple(), fcs = tuple()):
    keys = fc_s2l(keys)
    fcs = fc_s2l(fcs)
    class _Base(cls):
        def str(self):
            return str(self.__class__)
        def repr(self):
            return self.str()
        def __str__(self):
            return self.str()
        def __repr__(self):
            return self.repr()
        # def __call__(self, *a, **b):
        #     return self.call(*a, **b)
        # def call(self, *a, **b):
        #     return None
        def init(self, *a, **b):
            pass
        def __init__(self, *a, **b):
            sa = a[:lst]
            a = a[lst:]
            sb = {}
            for k in keys:
                if k in b:
                    sb[k] = b[k]
                    del b[k]
            super().__init__(*sa, **sb)
            self.init(*a, **b)
    for fc in fcs:
        base_fc = "__"+fc+"__"
        def _base_fc(obj, *a, **b):
            return getattr(obj, fc)(*a, **b)
        setattr(_Base, base_fc, _base_fc)
    return _Base

class Base:
    def str(self):
        return str(self.__class__)
    def __str__(self):
        return self.str()
    def __repr__(self):
        return self.__str__()
    def __init__(self, *args, **maps):
        self.init(*args, **maps)
    def __call__(self, *args, **maps):
        return self.call(*args, **maps)
    def init(self, *args, **maps):
        pass
    def call(self, *args, **maps):
        return self.deal(*args, **maps)
    def deal(self, *args, **maps):
        return None

pass

class WBase(Base):
    def _open(self):
        pass
    def open(self):
        self._open()
        return pyz.with_out(self.close, True)
    def _close(self):
        pass
    def close(self, exc_type, exc_val, exc_tb):
        self._close()

pass

class With(Base):
    def init(self, args=False):
        self.args = args
    def call(self, cls):
        def _open(obj):
            pass
        def open(obj):
            obj._open()
            return pyz.with_out(obj.close, self.args)
        def _close(obj):
            pass
        def close(obj):
            obj._close()
        cls._open = _open
        cls._close = _close
        cls.open = open
        cls.close = close
        return cls

pass

class Args(Base):
    @staticmethod
    def is_args(obj):
        return isinstance(obj, Args)
    @staticmethod
    def is_collect(obj):
        return Args.is_args(obj) or type(obj) in (list, tuple, dict)
    def __len__(self):
        return self.size()
    def as_dict(self, deep=False):
        mps = dict(self.dicts)
        if deep:
            rst = {}
            for k,v in mps.items():
                if isinstance(k, Args):
                    k = k.as_dict(deep)
                if isinstance(v, Args):
                    v = v.as_dict(deep)
                rst[k]=v
            mps = rst
        for it in self.lists:
            if isinstance(it, Args):
                if len(it.lists)!=len(it):
                    continue
                it = it.lists
            if len(it)!=2:
                continue
            if deep:
                it = [k if not isinstance(k, Args) else k.as_dict(deep) for k in it]
            mps[it[0]] = it[1]
        return mps
    def as_list(self, cmb=0, item_args = True, deep=False):
        lst = list(self.args)
        if deep:
            lst = [it if not isinstance(it, Args) else it.as_list(cmb, item_args, deep) for it in lst]
        mps = dict(self.dicts)
        for k,v in mps.items():
            if deep and isinstance(v, Args):
                v = v.as_list(cmb, item_args, deep)
            if isinstance(k, Args):
                k = k.as_list(cmb, item_args, deep)
            if cmb==0 or type(v)!=list:
                it = [k,v]
            else:
                v = list(v)
                v.append(k)
            if item_args:
                it = Args(v)
            lst.append(it)
        return lst
    def size(self):
        return len(self.args)+len(self.maps)
    def str(self):
        return f"<Args args={self.args}, maps={self.maps}>"
    @property
    def lists(self):
        return self.args
    @lists.setter
    def lists(self, val):
        self.args=val
    @lists.deleter
    def lists(self):
        del self.args
    @property
    def dicts(self):
        return self.maps
    @dicts.setter
    def dicts(self, val):
        self.maps=val
    @dicts.deleter
    def dicts(self):
        del self.maps
    def init(self, args, maps):
        self.args = args
        self.maps = maps
    def full(self, list_key = "list", dict_key = "dict"):
        rst = {}
        rst[list_key] = self.args
        rst[dict_key] = self.maps
        return rst
    def call(self, *a,**b):
        return self.full(*a,**b)


pass