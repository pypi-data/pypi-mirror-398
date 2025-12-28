#
from buildz import Base, xf
from ..ioc.decorator import decorator,IOCDObj
class Loads(IOCDObj):
    def init(self, conf, vtype = "envs", flush=False):
        if type(conf)==str:
            conf = xf.loads(conf)
        self._type = vtype
        self.conf = conf
        self.flush = flush
    def bind(self, wrap):
        super().bind(wrap)
        self.decorator.add_bind(self)
    def call(self):
        conf = self.decorator.obj
        confs = conf.confs
        maps = {}
        for key, val in self.conf.items():
            key = confs.gid(self.decorator.namespace, key)
            maps[key] = val
        if self._type in ('env', 'envs'):
            if self.flush:
                confs.flush_env(maps)
            xf.deep_fill(maps, conf.envs, 1)
        else:
            if self.flush:
                maps = xf.unflush_maps(maps, confs.id)
            confs.push_vars(maps)

pass

class Loadf(Loads):
    def init(self, fp, vtype="env"):
        conf = xf.loadf(fp)
        super().init(conf, vtype)

pass
decorator.regist("load_conf", Loads)
decorator.regist("loads_conf", Loads)
decorator.regist("loadf_conf", Loadf)