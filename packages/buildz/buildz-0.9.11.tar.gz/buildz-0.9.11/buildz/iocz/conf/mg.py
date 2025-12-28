
#
from ..ioc.mg import Manager, GetKey, Ids
from ... import dz,xf
from ..conf_deal.deal import DealDeal
from .unit import ConfUnit
spt = Ids(".")
class DLKey(GetKey):
    @staticmethod
    def Load(conf):
        keys, kfind = dz.dget(conf, spt("dict.key"))
        lids, lfind = dz.dget(conf, spt("list.index"))
        default, find = dz.dget(conf, 'default', None)
        return DLKey(keys, lids, default)
    def init(self, keys, indexes, default=None):
        super().init()
        self.keys = dz.tolist(keys)
        self.indexes = dz.tolist(indexes)
        self.default = default
    def list_get(self, conf):
        for indexes in self.indexes:
            obj, find = dz.dget(conf, indexes)
            if find:
                return obj, find
        return self.default, 0
    def dict_get(self, conf):
        for keys in self.keys:
            obj, find = dz.dget(conf, keys)
            if find:
                return obj, find
        return self.default, 0
    def call(self, conf):
        if dz.islist(conf):
            return self.list_get(conf)
        return self.dict_get(conf)
    def list_fill(self, conf, key):
        for indexes in self.indexes:
            obj, find = dz.dget(conf, indexes)
            if find:
                dz.dset(conf, indexes, key)
                return
        assert 0
    def dict_fill(self, conf, key):
        for keys in self.keys:
            obj, find = dz.dget(conf, keys)
            if find:
                dz.dset(conf, keys, key)
                return
        dz.dset(conf, self.keys[0], key)
    def fill(self, conf, key):
        if dz.islist(conf):
            self.list_fill(conf, key)
        else:
            self.dict_fill(conf, key)
default_conf = None
s_default_conf = r"""
    {
        id.spt: '.'
        env: {
            spt: '.'
            orders: [local, args, conf, sys]
        }
        conf:{
            dict.key = 'id'
            list.index = [(0,1)]
            default: null
        }
        deal: {
            spt: '.'
            dict.key = type
            list.index = ((0,0),0)
            default: null
        }
        tag: {
            dict.key='tag'
        }
    }
"""
def init():
    global default_conf
    if default_conf is not None:
        return
    default_conf = xf.loads(s_default_conf)
    default_conf = dz.flush_maps(default_conf)
class ConfManager(Manager):
    def init(self, conf=None):
        init()
        spt = Ids(".")
        if conf is None:
            conf = {}
        if type(conf)==str:
            conf = xf.loads(conf)
        conf = dz.flush_maps(conf)
        dz.fill(default_conf, conf, 0)
        id_spt, find = dz.dget(conf, spt("id.spt"),".")
        ids = Ids(id_spt)
        deal_spt, find = dz.dget(conf, spt("id.spt"), id_spt)
        deal_ids = Ids(deal_spt)
        env_ids, find = dz.dget(conf, spt("env.spt"), id_spt)
        deal_key = DLKey.Load(conf['deal'])
        conf_key = DLKey.Load(conf['conf'])
        tag_key = DLKey.Load(conf['tag'])
        env_orders, find = dz.dget(conf, spt("env.orders"), None)
        super().init(ids, deal_key, conf_key, tag_key, deal_ids, env_ids, env_orders)
        self.set_deal('deal', DealDeal())
    def add_conf(self, conf):
        unit = ConfUnit(conf, self)
        return unit

pass