#
from .base import *
from .datas import Datas
from .tdata import TagData, UnitBase
from .confs import Confs
from .encapes import Encapes
from ... import pyz
from .builds import Builds
from .envs import Envs
class Unit(UnitBase):
    def nsid(self, src=None, id=None):
        if src == -1:
            src = self
        if isinstance(src, UnitBase) or isinstance(src, TagData):
            src,id = src.ns, src.id
        return src, id
    def init(self, ns=None, deal_ns=None, env_ns=None, deal_key = None, conf_key = None, tag_key = None, id=None):
        super().init(ns, id)
        self.deal_ns = deal_ns
        self.env_ns = env_ns
        self.deal_key = deal_key
        self.conf_key = conf_key
        self.tag_key = tag_key
        self.confs = Confs(ns, deal_ns, id)
        self.deals = Datas(deal_ns, id)
        self.envs = Envs(env_ns, id)
        self.builds = Builds(self)
        self.mg = None
        self.build_encapes()
        self.vars = []
    def deal_vars(self):
        if self.mg is None or len(self.vars)==0:
            return
        for kvs, src, tag in self.vars:
            self.push_vars(kvs, src, tag)
        self.vars = []
    def add_build(self, conf):
        self.builds.add(conf)
    def build(self):
        self.builds.build()
    def is_conf(self, obj):
        return self.confs.is_conf(obj)
    def build_encapes(self):
        if self.confs is None or self.deals is None or self.deal_key is None:
            self.encapes = None
            return
        self.encapes = Encapes(self.ns, self.id, None, self)
    def bind(self, mg):
        if self.mg == mg:
            return
        self.mg = mg
        self.deal_key = pyz.nnull(self.deal_key, mg.deal_key)
        self.conf_key = pyz.nnull(self.conf_key, mg.conf_key)
        self.tag_key = pyz.nnull(self.tag_key, mg.tag_key)
        if self.id is None:
            self.id = mg.id()
            self.confs.set_id(self.id)
            self.deals.set_id(self.id)
            self.envs.set_id(self.id)
        self.mg.add(self)
        self.builds.bind(mg.builds)
        self.confs.bind(mg.confs)
        self.deals.bind(mg.deals)
        self.envs.bind(mg.envs)
        self.build_encapes()
        self.encapes.bind(mg.encapes)
        self.deal_vars()
    def lc_get_env(self, key, ns=None, tag=None, id=None):
        return self.envs.tget(key, ns, id, False)
    def get_env(self, key, src=-1, id=None, gfind=True):
        src, id = self.nsid(src, id)
        if not gfind:
            return self.lc_get_env(key, src, None, id)
        return self.mg.get_env(key, src, None, id, self.lc_get_env)
    def update_env(self, maps, tag=None, flush=False):
        self.envs.update(maps, tag, flush)
    def set_env(self, key, val, tag=None):
        self.envs.set(key, val, tag)
    def get_deal(self, key, src=-1, id=None, gfind=True):
        src, id = self.nsid(src, id)
        return self.deals.tget(key, src, id, gfind)
    def set_deal(self, key, deal, tag=None):
        self.deals.set(key, deal, tag)
    def get_conf(self, key, src=-1, id=None, gfind=True):
        src, id = self.nsid(src, id)
        return self.confs.tget(key, src, id, gfind)
    def set_conf(self, key, conf, tag=None):
        self.conf_key.fill(conf, key)
        self.confs.set(key, conf, tag)
    def tag(self, conf, _tag=None):
        if _tag is None:
            _tag, find = self.tag_key(conf)
        return _tag
    def add_conf(self, conf, tag = None):
        key,find = self.conf_key(conf)
        tag = self.tag(conf, tag)
        if find:
            self.set_conf(key, conf, tag)
    def get_encape(self, key, src=-1, id=None, gfind=True):
        src, id = self.nsid(src, id)
        self.mg.build()
        return self.encapes.tget(key, src, id, gfind)
    def set_encape(self, key, encape, tag=None):
        self.encapes.set(key, encape, tag)
    def get_var(self, key, src=-1, tag=None):
        src, id = self.nsid(src, None)
        return self.mg.get_var(key, src, tag)
    def push_vars(self, kvs, src=-1, tag=None):
        if self.mg is None:
            self.vars.append([kvs, src, tag])
            return
        src, id = self.nsid(src, None)
        return self.mg.push_vars(kvs, src, tag)
    def get(self, key, params=None, src=-1, id=None, gfind=True, search_var=True):
        src, id = self.nsid(src, id)
        if search_var:
            obj, find = self.mg.get_var(key, src, TagData.Key.Ns)
            if find:
                return obj, 1
        encape, _tag, find = self.get_encape(key, src, id, gfind)
        if not find:
            return None, 0
        return encape(params),1
    def get_obj(self, key, params=None, src=-1, id=None, gfind = True, search_var=True):
        return self.get(key, params, src, id, gfind, search_var)[0]