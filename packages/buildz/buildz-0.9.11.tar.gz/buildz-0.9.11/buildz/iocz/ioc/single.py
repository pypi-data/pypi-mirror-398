#
from ... import pyz,dz,Base

class Key:
    default_param_key = 'single_id'
    i_multi = 0
    i_single = 1
    i_param = 2
    multi='multi'
    single='single'
    param='param'
    str2int = {
        multi:i_multi,
        single: i_single,
        param: i_param
    }
    @staticmethod
    def s2i(key=None):
        if key is None:
            key = Key.i_single
        if key in Key.str2int:
            key = Key.str2int[key]
        return key
class Single(Base):
    Key = Key
    def init(self, single=None, param_key = None):
        if param_key is None:
            param_key = Key.default_param_key
        self.single = Key.s2i(single)
        self.objs = {}
        self.param_key = param_key
    def get_key(self, params):
        if self.single == Key.i_multi:
            return 0,0
        elif self.single == Key.i_single:
            key = None
        elif self.single == Key.i_param:
            if params is None:
                key = None
            else:
                key = params.get(self.param_key)
        else:
            assert 0
        return key,1
    def set(self, params, obj):
        key, find = self.get_key(params)
        if not find:
            return
        self.objs[key] = obj
    def get(self, params):
        key, find = self.get_key(params)
        if not find:
            return 0,0
        if key not in self.objs:
            return 0,0
        return self.objs[key],1