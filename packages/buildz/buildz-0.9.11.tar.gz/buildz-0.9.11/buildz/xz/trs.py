
from buildz import xf, Base
class Translate(Base):
    """
    数据映射
    conf:
    main: [
        null, mdict
        [

        ]
    ]
    main: [
        [data.total, total] // [data.total, total, key]
        [data.diff, datas, list, translates]
    ]
    or: 
    main: {
        data.total: total
        data.diff: [datas, list, translates]
    }
    translates: {
        ...
    }
    """
    def init(self, conf, src_spt=".",dst_spt = ".", inline = False, remove_src = False, vars = None):
        self.conf = conf
        self.src_spt = src_spt
        self.dst_spt = dst_spt
        self.inline = inline
        self.remove_src = remove_src
        self.cache_conf = {}
        self.vars = vars
    def kfc(self, fckey, val, vars=None):
        fc = self.var(fckey, vars)
        #print(f"[TESTZ] kfc: fckey: {fckey}, val: {val}, fc: {fc}")
        return fc(val)
    def var(self, key, vars=None):
        #print(f"[TESTZ] vars: {vars}")
        if vars is None:
            vars = self.vars
        #print(f"[TESTZ] vars: {vars}")
        if vars is None:
            raise Exception(f"var not found: {key}")
        if type(vars)==dict:
            if key not in vars:
                raise Exception(f"var not found: {key}")
            return vars[key]
        if callable(vars):
            return vars(key)
        return vars.get(key)
    def call(self, data, key = "main", vars=None):
        trs = xf.get(self.conf, key)
        #print(f"[TESTZ] trs: {trs}")
        trs = expand(trs)
        #print(f"[TESTZ] expand.trs: {trs}")
        return self.deal(data, trs,vars)
    def conf_get(self, key):
        if key in self.cache_conf:
            return self.cache_conf[key]
        assert key in self.conf
        rst = self.conf[key]
        rst = dict2list(rst)
        self.cache_conf[key] = rst
        return rst
    def src_get(self, data, key):
        if self.src_spt is not None:
            key = key.split(self.src_spt)
        return xf.gets(data, key)
    def dst_set(self, data, key, val):
        #print(f"[TESTZ] key: {key}")
        if self.dst_spt is not None:
            key = key.split(self.dst_spt)
        return xf.sets(data, key, val)
    def src_has(self, data, key):
        if self.src_spt is not None:
            key = key.split(self.src_spt)
        return xf.has(data, key)
    def src_remove(self, data, key):
        if self.src_spt is not None:
            key = key.split(self.src_spt)
        return xf.removes(data, key)
    def get_type(self, trs):
        if len(trs)==2:
            if type(trs[1]) not in (list, dict):
                return "key"
            return trs[0]
        return trs[2]
    def deal(self, data, trs, vars=None):
        """
            type: key, 
            conf = [
                key, target_key, type, info
            ]
            key: return [target_key, target_val, exists]
        """
        # trs = xf.get(conf, key)
        # trs = dict2list(trs)
        _type = self.get_type(trs)
        #print(f"[TESTZ] deal.trs: {trs}")
        if _type in ("list", "dict"):
            info = trs[-1]
            if type(info) == str:
                info = self.conf_get(info)
            trs[-1] = info
        if _type == "list":
            _trs = trs[-1]
            _trs = expand(_trs)
            if self.inline:
                rst = data
            else:
                rst = [None]*len(data)
            for i in range(len(data)):
                dt = data[i]
                _rst = self.deal(dt, _trs, vars)
                rst[i] = _rst
        elif _type == "dict":
            if self.inline:
                rst = data
            else:
                rst = {}
            for _trs in trs[-1]:
                #print(f"[TESTZ] _trs: {_trs}")
                _trs = expand(_trs)
                #print(f"[TESTZ] expand_trs: {_trs}")
                src_key, target_key = _trs[:2]
                _ctype = self.get_type(_trs)
                if _ctype == "val":
                    _rst = _trs[3]
                elif _ctype == "var":
                    _rst = self.var(_trs[3], vars)
                else:
                    if not self.src_has(data, src_key):
                        continue
                    val = self.src_get(data, src_key)
                    if _ctype == "key":
                        _rst = val
                    elif _ctype == "kfc":
                        _rst = self.kfc(_trs[3], val, vars)
                    else:
                        _rst = self.deal(val, _trs, vars)
                if self.inline and self.remove_src and _ctype not in ("val", "var"):
                    self.src_remove(data, src_key)
                    #del data[src_key]
                self.dst_set(rst, target_key, _rst)
                #rst[target_key] = _rst
        else:
            raise Exception("error")
        return rst
def dict2list(trs):
    if type(trs)==dict:
        tmp = []
        for k,v in trs.items():
            if type(v) not in [list, tuple]:
                v = [v]
            if type(v)==tuple:
                v = list(v)
            if len(v)==1:
                v = v+["key"]
            v = [k]+v
            tmp.append(v)
        trs = tmp
    return trs
def expand(trs):
    trs = dict2list(trs)
    if len(trs)>0:
        k = trs[0]
        if type(k) in (list, tuple):
            trs = ['dict', trs]
    if len(trs)>1:
        val = trs[-1]
        if type(val)==dict:
            trs[-1] = dict2list(val)
    return trs

pass