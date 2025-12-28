from ..iocz.conf import conf
from .. import Base, xf, dz,pyz
from .argz import *
"""
key:{
    src: [a,b,c]
    des: asdf
    need:1
    default: True
    default_value: 123
    remove: 1
}
key: [
    src, 
    [default, default_value]
    [des, need, remove]
]
"""
class ArgItemConf(conf.Conf):
    def init(self):
        super().init()
        self.index(0, 'src')
        self.key('src')
        df = conf.Conf()
        df.index(0, 'default')
        df.index(1, 'default_value')
        self.index(1,deal= df, dict_out=1)
        self.key('default', deal=df, dict_out=1)
        des = conf.Conf()
        des.index(0,'need')
        des.index(1, 'des')
        des.index(2, 'remove')
        self.index(2, deal=des, dict_out=1)

pass
class ArgSrcConf(conf.Conf):
    def init(self):
        super().init()
        self.index(0, 'key', need=1)
        self.key('key', 'val,value,data'.split(','), need=1)
        self.index(1, 'type')
        self.key('type', 'vtype'.split(","))
    def call(self, data, unit=None):
        data, upd = super().call(data, unit)
        val = data['key']
        if 'type' not in data:
            if type(val)==int:
                vtype = ArgType.list
            else:
                vtype = ArgType.dict
        else:
            vtype = data['type']
        data['type'] = ArgType.stand(vtype)
        return data, upd

class TrsArgsBuilder(Base):
    def init(self):
        self.conf = ArgItemConf()
        self.src_conf = ArgSrcConf()
    def visits(self, datas, vtype,obj):
        for key, item in dz.dict2iter(datas):
            item,_ = self.conf(item)
            it = ArgItem(key, vtype, *dz.g(item, need=0, default=0, default_value=None,des=None, remove=True))
            srcs = dz.g(item, src=[])
            if not dz.islist(srcs):
                srcs = [srcs]
            for src in srcs:
                src, _ = self.src_conf(src)
                key, vtype = src['key'], src['type']
                it.add(key, vtype)
            obj.add(it)
    def call(self, conf):
        lists = xf.g(conf, list={})
        dicts = xf.g(conf, dict={})
        if len(lists)+len(dicts)==0:
            return None
        keep,list_fill = xf.g(conf, keep=0, fill='exp')
        obj = TrsArgs([], keep, list_fill)
        self.visits(lists, ArgType.list, obj)
        self.visits(dicts, ArgType.dict, obj)
        return obj

class FullArgsBuilder(Base):
    def init(self):
        self.trs_build = TrsArgsBuilder()
        cf = conf.Conf()
        rcf = conf.Conf()
        rcf.index(0, 'base')
        rcf.index(1, 'last')
        rcf.index(2, 'min')
        cf.index(0, 'range', deal=rcf)
        cf.key('range', 'ranges'.split(","), deal=rcf)
        cf.index(1, 'list')
        cf.index(2, 'dict')
        cf.key('list', 'args,lists'.split(","))
        cf.key("dict", 'maps,dicts'.split(","))
        _cf = conf.Conf()
        _cf.index(0, 'keep')
        _cf.index(1, 'fill')
        _cf.key('fill', 'fill_type'.split(','))
        cf.index(3, deal=_cf, dict_out=1)
        self.conf = cf
    def call(self, conf):
        arr_args = ArrArgs()
        conf, upd = self.conf(conf)
        #print(f"BUILD conf: {conf}")
        ranges = dz.g(conf, range=None)
        if ranges is not None:
            base = ranges['base']
            if base is not None:
                last, min = dz.g(ranges, last=None,min=0)
                min = pyz.nnull(min, 0)
                range_args = RangeListArgs(base, last, min)
                arr_args.add(range_args)
        trs_args = self.trs_build(conf)
        if trs_args is not None:
            arr_args.add(trs_args)
        return arr_args
