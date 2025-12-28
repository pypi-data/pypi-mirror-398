from . import Base
import os,sys,json,time
class Key:
    first='first'
    ifirst = 0
    last= 'last'
    ilast = -1
    @staticmethod
    def check_first(val):
        return val in (Key.first, Key.ifirst)
    @staticmethod
    def check_last(val):
        return val in (Key.last, Key.ilast)
class Path(Base):
    Key = Key
    def init(self, **maps):
        self.paths = {}
        self.fcs = {}
        self.lasts = {}
        k = "check_abs"
        self.check_abs = True
        if k in maps:
            self.check_abs = maps[k]
            del maps[k]
        for k, v in maps.items():
            self.set(k, v)
    @staticmethod
    def dir(fp):
        return os.path.dirname(fp)
    @staticmethod
    def join(*a):
        return os.path.join(*a)
    @staticmethod
    def rjoin(path, *a):
        a = [k.strip() for k in a if k is not None and k.strip()!=""]
        if len(a)==0:
            return None
        if path is None:
            return os.path.join(*a)
        return os.path.join(path, *a)
    @staticmethod
    def rfp(paths, *a, last=-1, check_abs=False):
        a = [k.strip() for k in a if k is not None and k.strip()!=""]
        if len(a)==0:
            return None
        if check_abs and len(a)>0:
            f = a[0]
            if f[:1]=="/" or f.find(":")>0:
                return Path.join(*a)
        #print(f"[TESTZ] a: {a}, paths: {paths}")
        #fp = os.path.join(*a)
        for path in paths:
            _fp = Path.rjoin(path, *a)
            if os.path.exists(_fp):
                return _fp
        return Path.rjoin(paths[last], *a)
    def add(self, name, path, index=0):
        self.paths[name].insert(index, path)
    def set(self, name, paths, last = -1, curr = None):
        if type(paths) not in (list, tuple):
            paths = [paths]
        if curr is not None and None not in paths:
            if Key.check_first(curr):
                paths = [None]+paths
            elif Key.check_last(curr):
                paths.append(None)
            else:
                assert False
        self.paths[name] = paths
        self.lasts[name] = last
        def fc(*a):
            return self.rfp(paths, *a, last=last, check_abs=self.check_abs)
        self.fcs[name] = fc
    def __getattr__(self, name):
        return self.fcs[name]
    def call(self, *obj):
        return self.fcs[None](*obj)
        it = obj[0]
        fc = Path.join
        if type(it) in (list, tuple):
            assert len(it)==2
            k, fp = it
            fc = self.fcs[k]
        rst = []
        for it in obj:
            if type(it) in (list, tuple):
                assert len(it)==2
                rst.append(it[1])
            else:
                rst.append(it)
        return fc(*rst)

pass
