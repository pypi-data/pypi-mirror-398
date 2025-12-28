#
from ..ioc.base import Base, EncapeData,IOCError
from ..ioc.single import Single
from ..ioc.decorator import decorator, IOCDObj
from .base import FormatData,FormatDeal
from buildz import xf, pyz
from buildz import Base as Basez
import os
#g_obj_cid = '_buildz_ioc_conf_index'
dp = os.path.dirname(__file__)
join = os.path.join
class ObjectDeal(FormatDeal):
    """
        对象object:
            {
                id: id
                type: object
                source: 导入路径+调用方法/类
                single: 1 //是否单例，默认是，
                        //这里的单例是一个id对应一个实例，
                        //如果两个id用的同一个source，就是同一个source的两个对象
                // 构造函数
                construct:{
                    args: [
                        item_conf,
                        ...
                    ]
                    maps: {
                        key1: item_conf,
                        ...
                    }
                }
                //construct和args+maps，不能同时存在
                args: [
                    item_conf,
                    ...
                ]
                maps: {
                    key1: item_conf,
                    ...
                }
                // sets之前调用方法
                prev_call: item_conf
                // 对象变量设置属性
                sets: [
                    {key: key1, data: item_conf }
                    ...
                ]
                // sets之后调用
                call: item_conf
                // remove前调用
                remove: item_conf
                // remove后调用
                after_remove: item_conf
            }
        简写：
            [[object, id, single], source, args, maps, sets, calls] 
                sets: [[key1, item_conf], ...]
        极简:
            [object, source]
        例:
            [object, buildz.ioc.ioc.conf.Conf] //生成Conf对象
    """
    def init(self, fp_lists = None, fp_defaults = None, fp_cst = None, fp_set = None):
        self.singles = {}
        self.single = Single("single", "id", 1)
        self.sources = {}
        super().init("ObjectDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "obj_lists.js"),
            join(dp, "conf", "obj_defaults.js"))
        if fp_set is None:
            fp_set = join(dp, 'conf', 'obj_set_lists.js')
        if fp_cst is None:
            fp_cst = join(dp, 'conf', 'obj_cst_lists.js')
        self.fmt_set = FormatData(xf.loads(xf.fread(fp_set)))
        self.fmt_cst = FormatData(xf.loads(xf.fread(fp_cst)))
    def get_maps(self, maps, sid, id):
        if id is None:
            return None
        if sid not in maps:
            return None
        maps = maps[sid]
        if id not in maps:
            return None
        return maps[id]
    def set_maps(self, maps, sid, id, obj):
        if sid not in maps:
            maps[sid] = {}
        maps[sid][id] = obj
    def _deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        data = self.format(data)
        info = edata.info
        conf = edata.conf
        confs = edata.confs
        icst = None
        isets = None
        ivars = None
        if type(info) == dict:
            cid = xf.g(info, id=None)
            iargs, imaps = xf.g(info, args = None, maps = None)
            icst = {'args':iargs, 'maps':imaps}
            if iargs is None and imaps is None:
                icst = None
            isets = xf.g(info, sets = None)
            ivars = xf.g(info, vars=None)
        ids = self.single.get_ids(edata)
        id = xf.g(data, id = None)
        #print(f"obj.deal ids: {ids} for {data}")
        obj = self.single.get_by_ids(ids)
        if obj is not None:
            #raise IOCError(f"null for {ids}")
            return obj
        #source = xf.g(data, source=0)
        source = xf.g1(data, source=0, src=0)
        if source == 0:
            raise Exception(f"define object without 'source' key, {data}")
        source = self.get_obj(source, conf)
        if type(source)==str:
            fc = xf.get(self.sources, source, None)
        else:
            fc = source
        if fc is None:
            fc = pyz.load(source)
            self.sources[source]=fc
        cst = xf.g(data, construct = None)
        if cst is None:
            _args = xf.g(data, args = [])
            _maps = xf.g(data, maps = {})
            cst = [_args, _maps]
        cst = self.fmt_cst(cst)
        if icst is not None:
            xf.fill(icst, cst, 1)
        args = xf.g(cst, args=[])
        args = xf.im2l(args)
        maps = xf.g(cst, maps={})
        self.push_vars(conf, ivars)
        args = [self.get_obj(v, conf) for v in args]
        maps = {k:self.get_obj(maps[k], conf) for k in maps}
        obj = self.single.get_by_ids(ids)
        if obj is not None:
            return obj
        obj = fc(*args, **maps)
        self.single.set_by_ids(ids, obj)
        prev_call = xf.g(data, prev_call=None)
        if prev_call is not None:
            # TODO: 这边info透传不知道会不会有问题
            self.get_obj(prev_call, conf, obj, edata.info)
        sets = xf.g(data, sets=[])
        if type(sets)==list:
            tmp = {}
            for kv in sets:
                kv = self.fmt_set(kv)
                k = kv['key']
                v = xf.get_first(kv, "val", "data")
                tmp[k] = v
            sets = tmp
        if type(isets) == list:
            tmp = {}
            for kv in isets:
                kv = self.fmt_set(kv)
                k = kv['key']
                v = xf.get_first(kv, "val", "data")
                tmp[k] = v
            isets = tmp
        if isets is not None:
            xf.fill(isets, sets, 1)
        for k,v in sets.items():
            v = self.get_obj(v, conf, obj)#, edata.info)
            setattr(obj, k, v)
        call = xf.g(data, call=None)
        if call is not None:
            self.get_obj(call, conf, obj)#, edata.info)
        self.pop_vars(conf, ivars)
        #print(f"obj.deal ids: {ids} for {data}, rst: {obj}")
        return obj
    def remove(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        data = self.format(data)
        info = edata.info
        conf = edata.conf
        confs = edata.confs
        ids = self.single.get_ids(edata)
        obj = self.single.get_by_ids(ids)
        if obj is None:
            return None
        call = xf.g(data, remove=None)
        if call is not None:
            self.get_obj(call, conf, obj, edata.info)
        xf.removes(self.singles, ids)
        call = xf.g(data, after_remove=None)
        if call is not None:
            self.get_obj(call, conf, obj, edata.info)
        return None

pass
def update_set(maps):
    rst = {}
    for k,v in maps.items():
        if type(v)==str:
            v = xf.loads(v)
        rst[k] = v
    return rst

pass
def update_list(arr):
    rst = []
    for v in arr:
        if type(v)==str:
            v = xf.loads(v)
        rst.append(v)
    return rst

pass
ioc_conf_key = "_buildz_ioc_conf"
class IOCConf(Basez):
    def init(self, key = "_buildz_ioc_conf", ckey = "_buildz_ioc_conf_cls"):
        self.maps = {}
        self.cmaps = {}
    def get(self, cls, default):
        key = id(cls)
        if key not in self.cmaps:
            return default
        prv = self.cmaps[key]
        if prv!=cls:
            return default
        if key in self.maps:
            return self.maps[key]
        return default
    def unset(self, cls):
        key = id(cls)
        if key in self.cmaps:
            del self.cmaps[key]
            del self.maps[key]
    def set(self, cls, dt):
        key = id(cls)
        self.maps[key] = dt
        self.cmaps[key] = cls

pass
g_ioc_conf = IOCConf()
class IOCObjectAdd_(IOCDObj):
    def init(self, key, *arr):
        _arr = update_list(arr)
        self.key = key
        self._arr = _arr
    def call(self, cls):
        rst = {}
        rst = g_ioc_conf.get(cls, rst)
        _arr = []
        if self.key in rst:
            _arr = rst[self.key]
        _arr+=self._arr
        rst[self.key] = _arr
        g_ioc_conf.set(cls, rst)
        return cls

pass
class IOCObjectArgs(IOCObjectAdd_):
    def init(self, *arr):
        super().init("args", *arr)

pass
class IOCObjectMCall(IOCObjectAdd_):
    def init(self, *arr):
        # function, args, maps
        ks = "mcall,args,maps".split(",")
        _arr = []
        for item in arr:
            if type(item)==str:
                item = xf.loads(item)
            if type(item)==list:
                item = update_list(item)
                l = min(len(ks), len(item))
                _tmp = {}
                for i in range(l):
                    _tmp[ks[i]] = item[i]
                item = _tmp
            else:
                item = update_set(item)
            item['source'] = None
            item['type'] = "mcall"
            _arr.append(item)
        super().init("mcalls", *_arr)

pass
class IOCObjectSet_(IOCDObj):
    def init(self, key, **maps):
        _maps = update_set(maps)
        self._maps = {key:_maps}
    def call(self, cls):
        rst = {}
        rst = g_ioc_conf.get(cls, rst)
        xf.fill(self._maps, rst)
        g_ioc_conf.set(cls, rst)
        return cls

pass
class IOCObjectSet(IOCObjectSet_):
    def init(self, **maps):
        super().init("sets", **maps)

pass
class IOCObjectMap(IOCObjectSet_):
    def init(self, **maps):
        super().init("maps", **maps)

pass
class IOCObject(IOCDObj):
    KEYS = "id,args,maps,call,prev_call,single,remove,sets,after_remove,template,parent,temp".split(",")
    SET_KEYS = "maps,sets".split(",")
    def init(self, **maps):
        super().init()
        rst = update_set(maps)
        for key in self.SET_KEYS:
            if key not in maps:
                continue
            val = maps[key]
            for _k, _v in val.items():
                if type(_v)==str:
                    _v = xf.loads(_v)
                val[_k] = _v
        self._maps = rst
    def _set(self, key, **maps):
        sets = {}
        if key in self._maps:
            sets = self._maps[key]
        rst = update_set(maps)
        xf.fill(sets, rst)
        self._maps[key] = rst
        return self
    def map(self, **maps):
        return self._set("maps", **maps)
    def maps(self, **maps):
        return self.map(**maps)
    def set(self, **maps):
        return self._set("sets", **maps)
    def sets(self, **maps):
        return self.set(**maps)
    def call(self, cls):
        src = cls.__module__+"."+cls.__name__
        conf = {}
        conf = g_ioc_conf.get(cls, conf)
        xf.fill(self._maps, conf)
        conf['source'] = src
        conf['type'] = 'object'
        if 'mcalls' in conf and 'call' not in conf:
            conf['call'] = {'type': "calls", 'calls': conf['mcalls']}
        self.decorator.add_datas(conf)
        #conf[g_obj_cid] = self.decorator.add_datas(conf, self)
        g_ioc_conf.unset(cls)
        return cls

pass

#decorator.regist("IOCObject", IOCObject)
decorator.regist("obj", IOCObject)
decorator.regist("object", IOCObject)
decorator.regist("obj_set", IOCObjectSet)
decorator.regist("obj_map", IOCObjectMap)
decorator.regist("obj_arg", IOCObjectArgs)
decorator.regist("obj_mcall", IOCObjectMCall)
decorator.regist("obj_sets", IOCObjectSet)
decorator.regist("obj_maps", IOCObjectMap)
decorator.regist("obj_args", IOCObjectArgs)