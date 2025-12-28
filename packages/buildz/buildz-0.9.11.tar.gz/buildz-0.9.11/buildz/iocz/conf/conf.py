
from .base import *
from ... import dz
class Conf(Base):
    '''
        list to dict
    '''
    def init(self, v2l=True):
        self.lists = {}
        self.aliases = {}
        self.ranges = {}
        self.v2l = v2l
    @staticmethod
    def default(val):
        if val is None:
            val = [0, None]
        if not dz.islist(val):
            val = [1, val]
        return val
    def range(self, key, base, last=None, min = 0, default=None):
        self.ranges[key] = base,last,min,self.default(default)
        return self
    def ikey(self, index=None, key=None, aliases=[], need=False, remove=True, deal = None, dict_out = False, default=None):
        if index is not None:
            self.index(index, key, need, deal, dict_out, default)
        if key is not None:
            self.key(key, aliases, need, remove, deal, dict_out, default)
        return self
    def key(self, key, aliases=[], need=False, remove=True, deal = None, dict_out = False, default=None):
        self.aliases[key] = list(aliases), need, remove, deal, dict_out, self.default(default)
        return self
    def index(self, i, key=None, need=False, deal = None, dict_out = False, default=None):
        self.lists[i] = key,need,deal, dict_out, self.default(default)
        return self
    def range_to_dict(self, rst, conf, unit=None):
        for key, item in self.ranges.items():
            base,last,min,default = item
            if last is None:
                tmp = conf[base:]
            else:
                tmp = conf[base:last]
            if len(tmp)<min:
                if default[0]:
                    val = default[1]
                else:
                    assert 0,f"require key '{key}' not set in list {conf}"
            else:
                val = tmp
            rst[key] = val
    def to_dict(self, conf, unit=None):
        if not dz.islist(conf):
            if not dz.isdict(conf) and self.v2l:
                conf = [conf]
            else:
                return conf, False
        rst = {}
        for i,item in self.lists.items():
            key, need, deal, out_dict, default = item
            if i>=len(conf):
                if default[0]:
                    val = default[1]
                else:
                    assert not need, f"require key '{key}' not set in list {conf}"
                    continue
            else:
                val = conf[i]
            if deal is not None:
                val,upd = deal(val, unit)
            if type(val)==dict and out_dict:
                rst.update(val)
            else:
                rst[key] = val
        self.range_to_dict(rst, conf, unit)
        return rst, 1
    def update_dict(self, conf, unit=None):
        upd = False
        for key, item in self.aliases.items():
            aliases, need, remove, deal, dict_out, default = item
            if key not in conf:
                for name in aliases:
                    if name in conf:
                        conf[key] = conf[name]
                        upd = 1
                        if remove:
                            del conf[name]
                        break
            if key not in conf:
                if default[0]:
                    conf[key] = default[1]
                else:
                    assert not need, f"require key '{key}' not set in dict {conf}"
            if key in conf and deal is not None:
                conf[key], _upd = deal(conf[key], unit)
                upd = upd or _upd
            if key in conf:
                val = conf[key]
                if dz.isdict(val) and dict_out:
                    dz.fill(val, conf, 1)
        return upd
    def call(self, conf, unit=None):
        conf, upd = self.to_dict(conf, unit)
        upd = upd or self.update_dict(conf, unit)
        return conf, upd

pass

