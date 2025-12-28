#

from .base import *
from .encapes import Encapeset
from .dataset import Dataset
from .vars import Varset
from ... import pyz,dz
from .ids import Ids
from .unit import Unit
from .builds import Buildset
from .sys_envs import SysEnvs
class GetKey(Base):
    def call(self, conf):
        return None, 0
    def fill(self, conf, key):
        assert 0,'not callable'
class SimpleConfKey(Base):
    def init(self, key):
        self.key = key
    def call(self, conf):
        if self.key not in conf:
            return None,0
        return conf[self.key],1
    def fill(self, conf, key):
        conf[self.key] = key

pass
class EnvKey:
    sys = 'sys'
    args = 'args'
    conf = 'conf'
    local = 'local'
    default_orders = [local, args, conf, sys]
class Manager(Base):
    EnvKey = EnvKey
    @staticmethod
    def make_key(key):
        if type(key) == str:
            key = SimpleConfKey(key)
        return key
    @staticmethod
    def make_ids(ids):
        if type(ids)==str:
            ids = Ids(ids)
        return ids
    def get_env(self, key, ns = None, tag = None, id = None, local_get = None):
        fcs = self.get_env_fcs
        fcs[EnvKey.local] = local_get
        for order in self.env_orders:
            fc = fcs[order]
            if fc is None:
                continue
            obj, _tag, find = fc(key, ns, tag, id)
            if find:
                return obj, _tag, find
        return None, None, 0
    def set_env_args(self, key, val, ns=None):
        self.sys_env.set(key, val, ns)
    def init(self, ids, deal_key='type', conf_key='id', tag_key='tag', deal_ids = None, env_ids = None, env_orders = None):
        if env_orders is None:
            env_orders = EnvKey.default_orders
        self.env_orders = env_orders
        self._index = 0
        self.units = {}
        self.builds = Buildset(self)
        ids = self.make_ids(ids)
        self.ids = ids
        self.deal_key = self.make_key(deal_key)
        self.conf_key = self.make_key(conf_key)
        self.tag_key = self.make_key(tag_key)
        self.deal_ids = self.make_ids(pyz.nnull(deal_ids, ids))
        self.env_ids = self.make_ids(pyz.nnull(env_ids, ids))
        self.confs = Dataset(self.ids)
        self.envs = Dataset(self.env_ids)
        self.sys_envs = SysEnvs(self.env_ids)
        self.args_envs = Dataset(self.env_ids)
        self.deals = Dataset(self.deal_ids)
        self.encapes = Encapeset(self.ids, self)
        self.vars = Varset(self.ids)
        #
        self.set_env_args = self.args_envs.set
        self.update_env_args = self.args_envs.update
        self.update_env = self.envs.update
        self.set_env = self.envs.set
        #self.get_env = self.envs.tget
        self.get_env_fcs = {
            EnvKey.sys: self.sys_envs.tget,
            EnvKey.args: self.args_envs.tget,
            EnvKey.conf: self.envs.tget
        }
        #
        self.push_var = self.vars.vpush
        self.push_vars = self.vars.vpushs
        self.pop_var = self.vars.vpop
        self.pop_vars = self.vars.vpops
        self.set_var = self.vars.vset
        self.set_vars = self.vars.vsets
        self.get_var = self.vars.vget
        self.unset_var = self.vars.vremove
        self.unset_vars = self.vars.vremoves
        #
        self.default_unit = self.create()
    def add_build(self, conf):
        self.builds.add(conf)
    def build(self):
        self.builds.build()
    def add(self, unit):
        unit.bind(self)
        self.units[unit.id] = unit
    def create(self, ns=None, deal_ns = None, env_ns = None, deal_key=None, conf_key= None):
        id = self.id()
        deal_key = pyz.nnull(deal_key, self.deal_key)
        conf_key = pyz.nnull(conf_key, self.conf_key)
        deal_key = self.make_key(deal_key)
        conf_key = self.make_key(conf_key)
        unit = Unit(ns, deal_ns, env_ns, deal_key, conf_key, id)
        unit.bind(self)
        return unit
    def get_unit(self, id):
        if id not in self.units:
            return self.default_unit
        return self.units[id]
    def id(self):
        index = self._index
        self._index+=1
        return index
    def get_deal(self, key, ns=None, id=None):
        return self.deals.tget(key, ns, id)
    def set_deal(self, key, deal, ns=None, tag=None, id=None):
        self.deals.set(key, deal, ns, tag, id)
    def get_conf(self, key, ns=None, id=None):
        return self.confs.tget(key, ns, id)
    def set_conf(self, key, conf, ns=None, tag=None, id=None):
        self.confs.set(key, conf, ns, tag, id)
    def get_encape(self, key, ns=None, id=None):
        self.build()
        return self.encapes.tget(key, ns, id)
    def set_encape(self, key, encape, ns=None, tag=None, id=None):
        self.encapes.set(key, encape, ns, tag, id)
    def get(self, key, ns=None, params=None, id=None, search_var = True):
        if search_var:
            obj, find = self.get_var(key, ns)
            if find:
                return obj, 1
        encape, tag, find = self.get_encape(key, ns, id)
        if not find:
            return None, 0
        return encape(params),1
    def get_obj(self, key, ns=None, params=None, id=None, search_var=True):
        return self.get(key, ns, params, id, search_var)[0]



pass
