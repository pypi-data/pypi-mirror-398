
from .base import *
from ... import dz
from ..ioc.single import Single
class ObjectEncape(BaseEncape):
    key_single = Single.Key.default_param_key
    @staticmethod
    def set_single_id(params, id):
        params.set(ObjectEncape.key_single, id)
        return params
    '''
        id=?
        
    '''
    def init(self, single, src, args, maps, sets, before_set=None, after_set=None):
        super().init()
        self.single = Single(single,ObjectEncape.key_single)
        self.src, self.args, self.maps, self.sets = src, args, maps, sets
        self.before_set = before_set
        self.after_set = after_set
        self.objs = {}
    def call(self, params=None, **maps):
        obj, find = self.single.get(params)
        if find:
            return obj
        src = self.obj(self.src, params)
        if type(src)==str:
            src = self.load(src)
        args = self.elist2obj(self.args,params)
        _maps = self.edict2obj(self.maps,params)
        obj = src(*args, **_maps)
        obj_conf = Params.Clone(params, obj=obj)
        self.obj(self.before_set, obj_conf)
        sets = self.edict2obj(self.sets, params, False)
        for k,v in sets:
            setattr(obj, k, v)
        self.obj(self.after_set, obj_conf)
        self.single.set(params, obj)
        return obj
class ObjectDeal(BaseDeal):
    def deal(self, conf, unit):
        assert 'source' in conf
        id,id_find = unit.conf_key(conf)
        single = dz.g(conf, single=None)
        if single is None and not id_find:
            single = Single.Key.multi
        src = dz.g(conf, source=None)
        before_set, after_set = dz.g(conf, before_set=None, after_set=None)
        before_set = self.get_encape(before_set, unit)
        after_set = self.get_encape(after_set, unit)
        if Confs.is_conf(src):
            src = unit.get_encape(src, unit)
        elif type(src)==str:
            src = self.load(src)
        args = self.get_elist(unit, conf, 'args', [])
        maps = self.get_edict(unit, conf, 'maps', {})
        sets = self.get_edict(unit, conf, 'sets', [])
        encape = ObjectEncape(single, src, args, maps, sets,before_set,after_set)
        return encape

pass