#
from buildz import Base, xf,pyz
class Build(Base):
    def init(self, *binds):
        self.builder = None
        self.binds = binds
    def bind(self, builder):
        self.builder = builder
        for obj in self.binds:
            obj.bind(builder)
    def call(self, conf):
        assert 0, 'not impl'
class Builder(Base):
    def init(self, fc = None, key_id = "id", default_key = "main"):
        self.vars = {}
        self.confs = {}
        self.key_id = key_id
        self.df_key = default_key
        self.set_fc(fc)
    def set_fc(self, fc):
        fc.bind(self)
        self.fc = fc
        return self
    def var(self, key, obj):
        self.vars[key] = obj
        return self
    def get_var(self, key):
        return self.vars[key]
    def get_conf(self, key):
        if type(key) == dict:
            conf = key
        else:
            if key not in self.confs:
                return self.get_var(key)
            conf = self.confs[key]
        return self.fc(conf)
    def conf(self, data):
        if type(data) == dict:
            tp = xf.g(data, type=None)
            if tp is not None and type(tp) not in (list, tuple, dict):
                if self.key_id not in data:
                    data[self.key_id] = self.df_key
                data = [data]
        if type(data) in (list, tuple):
            rst = {}
            for it in data:
                if self.key_id not in it:
                    continue
                id = it[self.key_id]
                rst[id] = it
            data = rst
        self.confs = data
        return self
    def call(self, data, key=None):
        key = pyz.nnull(key, self.df_key)
        return self.conf(data).get_conf(key)
