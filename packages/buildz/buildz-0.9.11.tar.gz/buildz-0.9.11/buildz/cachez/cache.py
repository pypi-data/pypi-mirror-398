#

from .. import xf, fz
from .. import ioc
from ..base import Base
from ..ioc import wrap
from .. import logz
ns = wrap.ns("buildz.cache")
import os,re,json


@ns.obj(id="cache.save")
@ns.obj_args("ref, cache.file", "ref, log")
class Save(Base):
    def init(self, cache, log, fkey = "cache.save", fp = None):
        self.fkey = fkey
        self.cache = cache
        self.log = log.tag("Cache.Save")
        self.fp = fp
    def save(self):
        fp = self.fp
        if fp is None:
            self.log.warn(f"cache not save cause 'cache.save' is None")
            return False
        fz.makefdir(fp)
        rst  = self.cache.data
        rs = xf.dumps(rst, format=True).encode("utf-8")
        fz.write(rs, fp, 'wb')
        return True
    def call(self, maps, fp):
        fp = xf.get(maps, self.fkey, None)
        fp = self.cache.rfp(fp)
        self.fp = fp
        return self.save()

pass
class CacheKey(Base):
    def init(self, cache, key):
        self.cache = cache
        self.key = key
    def has(self):
        return self.cache.has(self.key)
    def set(self, val):
        return self.cache.set(self.key, val)
    def get(self):
        return self.cache.get(self.key)
    def call(self, *args):
        if len(args)==0:
            return self.get()
        elif len(args)==1:
            return self.set(args[0])
        else:
            assert 0
@ns.obj(id="cache.file")
@ns.obj_args("ref, fps, cache.js","ref, log, null", "ref, rfp.current.first, false", "ref, split, .", "ref, key.currents, buildz.cache.path.currents", "ref, key.basedir, buildz.cache.path.basedir", "ref, save.index, -1", "ref, save.auto, false")
class Cache(Base):
    def clean(self):
        self.data = {}
    def bind(self, key):
        return CacheKey(self, key)
    def has(self, key):
        ks = key.split(self.spt)
        return xf.has(self.data, ks)
    def get(self, key):
        ks = key.split(self.spt)
        return xf.gets(self.data, ks)
    def set(self, key, val):
        xf.sets(self.data, key.split(self.spt), val)
        if self.auto_save:
            self.save()
    def remove(self, key):
        xf.removes(self.data, key.split(self.spt))
    def init(self, fps="cache.js", log=None, current_first=False, spt = ".", key_currents = "buildz.cache.path.currents", key_basedir = "buildz.cache.path.basedir", save_index = -1, auto_save = False, load_replace=False, save_json = False):
        self.save_json = save_json
        if type(fps) not in (tuple, list):
            fps = [fps]
        self.fps = fps
        self.spt = spt
        self.current_first = current_first
        self.log = logz.make(log)(self)
        self.key_currents = key_currents
        self.key_basedir = key_basedir
        self.save_index = save_index
        self.load_replace = load_replace
        self.data = {}
        self.auto_save = auto_save
    def set_currents(self, dp):
        if type(dp)!=list:
            dp = [dp]
        self.set(self.key_currents, dp)
    def add_currents(self, dp):
        dps = self.get_currents()
        if dps is None:
            dps = []
        if dp in dps:
            return
        dps.append(dp)
        self.set_currents(dps)
    def get_currents(self):
        dps = self.get(self.key_currents)
        if dps is None:
            dps = []
        if type(dps)!=list:
            dps = [dps]
        return dps
    def set_basedir(self, dp):
        self.set(self.key_basedir, dp)
    def get_basedir(self):
        return self.get(self.key_basedir)
    def rfp(self, fp):
        if fz.is_abs(fp):
            return fp
        dps = [None,"."]
        cfps = self.get_currents()
        if cfps is not None:
            if self.current_first:
                dps = cfps+dps
            else:
                dps = dps+cfps
        basedir = self.get_basedir()
        if basedir is not None:
            dps = [basedir]+dps
        for dp in dps:
            _fp = fp
            if dp is not None:
                _fp = os.path.join(dp, fp)
            if os.path.isfile(_fp):
                return _fp
        if basedir is not None:
            fp = os.path.join(basedir, fp)
        return fp
    def save(self, fp = None, save_json=None):
        if fp is None:
            fp = self.fps[self.save_index]
        fp = self.rfp(fp)
        fz.makefdir(fp)
        rst = self.data
        if save_json is None:
            save_json = self.save_json
        if save_json:
            rs = json.dumps(rst, indent=4, ensure_ascii= False).encode("utf-8")
        else:
            rs = xf.dumps(rst, format=True).encode("utf-8")
        fz.write(rs, fp, 'wb')
    def load(self, fps = None):
        if fps is None:
            fps = self.fps
        data = {}
        for fp in fps:
            fp = self.rfp(fp)
            if os.path.isfile(fp):
                self.log.info(f"load cache from {fp}")
                xdata = xf.flush_maps(xf.loadf(fp),visit_list=True)
                xf.fill(xdata, data, replace=self.load_replace)
        xf.fill(data, self.data, replace=0)
    def update(self, conf):
        conf = xf.flush_maps(conf,visit_list=True)
        xf.fill(conf, self.data, replace=1)

pass

@ns.obj(id="cache.mem")
@ns.obj_args("ref, log, null")
class Mem(Cache):
    def init(self, log=None):
        super().init(None, log)

pass
@ns.obj(id="cache")
@ns.obj_args("ref, cache.mem", "ref, cache.file")
class Caches(Base):
    def init(self, mem, cache):
        self.cache = cache
        self.mem = mem
        self.caches = [mem, cache]
        self.set = mem.set
        self.update = mem.update
        self.remove = cache.remove
        self.call=cache.call
        self.rfp = cache.rfp
        self.get_currents = cache.get_currents
        self.add_currents = cache.add_currents
        self.set_currents = cache.set_currents
        self.set_basedir = cache.set_basedir
        self.get_basedir = cache.get_basedir
        self.save = cache.save
        self.load = cache.load
        self.has_file = cache.has
        self.has_mem = mem.has
    def get_file(self, key):
        return self.cache.get(key)
    def get_mem(self, key):
        return self.mem.get(key)
    def set_file(self, key, val):
        self.cache.set(key,val)
    def set_mem(self, key, val):
        self.mem.set(key, val)
    def remove_file(self, key):
        self.cache.remove(key)
    def remove_mem(self, key):
        self.mem.remove(key)
    def get(self, key):
        for cache in self.caches:
            if cache.has(key):
                return cache.get(key)
        return None
    def has(self, key):
        for cache in self.caches:
            if cache.has(key):
                return True
        return False

pass