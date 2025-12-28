#
from ..tools import *
from buildz.ioc import wrap
import os
from buildz.db.dv import build
@wrap.obj(id="dbs")
@wrap.obj_args("ref, cache", "ref, log")
class Dbs(Base):
    def init(self, cache, log):
        self.cache = cache
        self.log = log.tag("Dbs")
        self.dbs = {}
    def call(self, maps, fp):
        confs = xf.g(maps, dbs={})
        for key,conf in confs.items():
            url,user,pwd,dv = xf.g(conf, url=None, user=None, pwd=None, device=key)
            dv = build(dv, [url, user, pwd], conf)
            dv.begin()
            self.dbs[key] = dv
        self.cache.set_mem("dbs", self.dbs)
        return True

pass

@wrap.obj(id="dbs.close")
@wrap.obj_sets(cache="ref, cache", log="ref, log")
class DbsClose(Base):
    def call(self, maps, fp):
        dbs = self.cache.get_mem("dbs")
        if dbs is None:
            return True
        for k,dv in dbs:
            dv.close()
        return True

pass

