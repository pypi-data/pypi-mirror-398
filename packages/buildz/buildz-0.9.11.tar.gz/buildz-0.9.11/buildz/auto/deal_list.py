#
from ..tools import *
from buildz.ioc import wrap
import os
@wrap.obj(id="deal.list")
@wrap.obj_args("ref, cache", "ref, log", "ref, cache.modify", "ref, list")
class List(Base):
    def init(self, cache, log, upd, lst):
        self.cache = cache
        self.log = log.tag("List")
        self.upd = upd
        self.lst = lst
    def call(self, data, fc):
        data = self.upd(data)
        fp = xf.g(data, file = None)
        if fp is not None:
            fp = self.cache.rfp(fp)
        datas = xf.g(data, datas=[])
        if fp is not None and os.path.isfile(fp):
            datas = xf.loadf(fp)
        if type(datas)==dict:
            datas = xf.g(datas, datas=[])
        deal = self.lst.curr()
        #print(f"List.datas: {xf.dumps(datas,format=1,deep=1)}")
        for data in datas:
            if not deal(data):
                self.log.error(f"failed in data: {data}")
                return False
        return True

pass


