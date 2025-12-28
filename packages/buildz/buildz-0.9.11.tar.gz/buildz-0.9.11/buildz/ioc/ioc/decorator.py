#coding=utf-8
from buildz.base import Base
from buildz import xf
from threading import Lock
class Fcs(Base):
    def init(self, wrap, fcs):
        self._ioc_args = [wrap, fcs]
        self._base = wrap
    @property
    def conf(self):
        return self._ioc_args[0].obj
    def __getattr__(self, key):
        return self._ioc_args[1][key]

pass
class IOCDObj(Base):
    def init(self):
        self._wrap = None
    def bind(self, wrap):
        self._wrap = wrap
        return self
    @property
    def wrap(self):
        return self._wrap
    @property
    def decorator(self):
        return self._wrap

pass
class IOCDWrap(Base):
    def init(self, fc, wrap):
        self.wrap = wrap
        while isinstance(fc, IOCDWrap):
            fc = fc.fc
        self.fc = fc
    def call(self, *args, **maps):
        fc = self.fc(*args, **maps)
        if isinstance(fc, IOCDObj):
            fc.bind(self.wrap)
        return fc
        #return self.fc(*args, **maps).bind(self.wrap)

pass
class Decorator(Base):
    """
        用@备注的形式自动生成conf文档
    """
    @property
    def namespace(self):
        return self.ns
    def init(self, ns=None, lock = False):
        self.conf = {}
        self.ns = ns
        self.fcs = {}
        self.obj_fcs = Fcs(self, self.fcs)
        self.obj = None
        self.id = None
        self.bind_fcs = []
        self.do_lock = lock
        if lock:
            self.lock = Lock()
            self.set = self.lk_fc(self.set)
            self.get = self.lk_fc(self.get)
            self.add = self.lk_fc(self.add)
            self.add_bind = self.lk_fc(self.add_bind)
    def add_bind(self, fc):
        fc = IOCDWrap(fc, self)
        self.bind_fcs.append(fc)
    def lk_fc(self, fc):
        def _fc(*a, **b):
            with self.lock:
                return fc(*a, **b)
        return _fc
    def bind(self, confs):
        self.conf['namespace'] = self.ns
        #from buildz import xf
        #print(f"[TESTZ] Decorator conf: {self.conf}")
        self.id = confs.add(self.conf)
        self.obj = confs.get_conf(self.id)
        for fc in self.bind_fcs:
            fc()
    def call(self):
        return self.obj_fcs
    def regist(self, key, fc):
        fc = IOCDWrap(fc, self)
        self.fcs[key]=fc
    def clone(self, ns=None, lock=None):
        if lock is None:
            lock = self.do_lock
        dc = Decorator(ns, lock)
        for k,fc in self.fcs.items():
            dc.regist(k, fc)
        for fc in self.bind_fcs:
            dc.add_bind(fc)
        return dc
    def get(self, tag, index):
        conf = self.conf
        if tag not in conf:
            conf[tag]=[]
        return conf[tag][index]
    def add(self, tag, data):
        conf = self.conf
        if tag not in conf:
            conf[tag]=[]
        id = len(conf[tag])
        conf[tag].append(data)
        return id
    def set(self, tag, key, val):
        conf = self.conf
        if tag not in conf:
            conf[tag]={}
        conf[tag][key]=val
    def add_datas(self, item):
        if type(item)==str:
            item = xf.loads(item)
        return self.add("datas", item)
    def get_datas(self, id):
        return self.get("datas", id)
    def set_datas(self, id, val):
        return self.set("datas", id, val)
    def set_envs(self, key, val):
        return self.set("env", key, val)
    def add_inits(self, val):
        return self.add("inits", val)
    def add_locals(self, item):
        return self.add("locals", item)

pass

class Decorators(Base):
    decorator_fc_names = "regist,get,add,set,add_datas,get_datas,set_datas,set_envs,add_inits,add_locals".split(",")
    def init(self, ns=None):
        self.demo = Decorator(ns)
        self.ns = ns
        self.confs = {}
        self.confs[ns] = self.demo
        self.obj = None
        for nfc in Decorators.decorator_fc_names:
            setattr(self, nfc, self.ns_fc(nfc))
    def ns_fc(self, nfc):
        def _fc(*a, ns=None):
            return getattr(self.decorator(ns), nfc)(*a)
        return _fc
    def decorator(self, ns=None):
        if ns is None:
            ns = self.ns
        if ns not in self.confs:
            self.confs[ns] = self.demo.clone(ns)
        return self.confs[ns]
    def call(self, ns=None):
        return self.decorator(ns)()
    def bind(self, confs):
        for ns, conf in self.confs.items():
            conf.bind(confs)
        self.obj = confs

pass
decorators = Decorators()
decorator = decorators.demo
ns = decorators
# class Decorator(Base):
#     def init(self):
#         #self.conf = {}
#         self.confs = {}
#         self.confs[None] = {}
#         self.objs = {}
#         self.ids = {}
#         self.namespace = None
#         self.fcs = {}
#         self._ns = {}
#         self.regist("add_datas", self.add_datas)
#     def get_conf_obj(self, ns):
#         return self.objs[ns]
#     @property
#     def conf(self):
#         return self.get_conf_obj(self.namespace)
#     def fcns(self, namespace, fc):
#         self._ns[fc] = namespace
#     def ns(self, namespace):
#         self.namespace = namespace
#     def curr_ns(self):
#         return self.namespace
#     def regist(self, key, fc):
#         self.fcs[key] = fc
#     def get_conf(self, src, ns = None):
#         if ns is None:
#             ns = self.namespace
#         if src in self._ns:
#             ns = self._ns[src]
#         if ns not in self.confs:
#             conf = {}
#             conf['namespace'] = ns
#             self.confs[ns] = conf
#         return self.confs[ns]
#     def get(self, tag, index, src=None):
#         conf = self.get_conf(src)
#         if tag not in conf:
#             conf[tag]=[]
#         return conf[tag][index]
#     def add(self, tag, data, src = None, ns = None):
#         conf = self.get_conf(src, ns)
#         if tag not in conf:
#             conf[tag]=[]
#         id = len(conf[tag])
#         conf[tag].append(data)
#         return id
#     def set(self, tag, key, val, src=None):
#         conf = self.get_conf(src)
#         if tag not in conf:
#             conf[tag]={}
#         conf[tag][key]=val
#     def add_datas(self, item, key=None, ns = None):
#         if type(item)==str:
#             item = xf.loads(item)
#         return self.add("datas", item, key, ns)
#     def get_datas(self, id, key=None):
#         return self.get("datas", id, key)
#     def set_datas(self, id, val):
#         return self.set("datas", id, val)
#     def set_envs(self, key, val):
#         return self.set("env", key, val)
#     def add_inits(self, val):
#         return self.add("inits", val)
#     def add_locals(self, item):
#         return self.add("locals", item)
#     def bind_confs(self, confs):
#         for ns, val in self.confs.items():
#             id = confs.add(val)
#             obj = confs.get_conf(id)
#             self.ids[ns] = id
#             self.objs[ns] = obj
#     def all(self):
#         arr = [val for k,val in self.confs.items()]
#         return arr
#     # def call(self):
#     #     return self.conf

# pass

# decorator = Decorator()
# class Fcs:
#     def __init__(self, k, ns):
#         self._ioc_ns = [k, ns]
#     @property
#     def conf(self):
#         return self._ioc_ns[1].get_conf(self._ioc_ns[0])

# pass
# class NameSpace(Base):
#     def get_conf(self, ns):
#         return self.decorator.get_conf_obj(ns)
#     def init(self, decorator):
#         self.decorator = decorator
#         self.lock = Lock()
#     def fc(self, namespace, rfc):
#         def wfc(*a, **b):
#             with self.lock:
#                 ns = self.decorator.curr_ns()
#                 self.decorator.ns(namespace)
#                 rst = rfc(*a,**b)
#                 self.decorator.fcns(namespace, rst)
#                 self.decorator.ns(ns)
#                 return rst
#         return wfc
#     def call(self, namespace):
#         fcs = self.decorator.fcs
#         obj = Fcs(namespace, self)
#         for k,f in fcs.items():
#             setattr(obj, k, self.fc(namespace, f))
#         def wfc(rfc, *a, **b):
#             with self.lock:
#                 ns = self.decorator.curr_ns()
#                 self.decorator.ns(namespace)
#                 rst = rfc(*a,**b)
#                 self.decorator.fcns(namespace, rst)
#                 self.decorator.ns(ns)
#                 return rst
#         setattr(obj, "wrap", wfc)
#         return obj

# pass
# ns = NameSpace(decorator)
