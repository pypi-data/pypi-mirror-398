#
from ..tools import *
from buildz.ioc import wrap
#print(f"warp.obj_sets: {wrap.obj_sets}")
#raise Exception("test")
@wrap.obj(id="save")
@wrap.obj_args("ref, cache", "ref, log", "ref, cache.modify")
@wrap.obj_sets(cache_save = "ref, cache.save")
class Save(Base):
    def init(self, cache, log, upd):
        self.cache = cache
        self.log = log.tag("Save")
        self.upd = upd
    def call(self, data, next_fc=None):
        data = self.upd(data)
        save = xf.g(data, save={})
        fsave = xf.get(data, "save.file", {})
        mem = xf.get(data, "save.mem", {})
        saves = [save, fsave, mem]
        fcs = [self.cache.set, self.cache.set_file, self.cache.set_mem]
        for save,fc in zip(saves,fcs):
            for k, v in save.items():
                if type(v)==str:
                    v = ["key"]+v.split(".")
                if type(v)!=list:
                    v = ["key", v]
                tp = v[0]
                v = v[1:]
                if tp=="eval":
                    val = eval(v[0])
                elif tp == "exec":
                    exec(v[0])
                    val = self.val
                else:
                    val = xf.gets(data, v)
                fc(k, val)
        save = saves[0]
        if len(save)+len(fsave)>0:
            sv = self.cache_save.save()
            self.log.debug(f"cache_save in save: {sv}")
        return next_fc(data)

pass


