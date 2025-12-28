#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class MethodCallDeal(FormatDeal):
    """
    对象方法调用:
        {
            id: id
            type: mcall
            source: 对象id
            mcall|method: 调用方法
            vars: [...]
            args: [...]
            maps: {key:...}
            info: item_conf，额外引用信息，默认null
        }
    简写:
        [[mcall, id], source, method, args, maps, info]
        [mcall, method]
    
    例:
        [mcall, obj.test, run] // 调用
    """
    def init(self, fp_lists = None, fp_defaults = None):
        self.singles = {}
        self.sources = {}
        super().init("MethodCallDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "mcall_lists.js"),
            join(dp, "conf", "mcall_defaults.js"))
    def _deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        conf = edata.conf
        data = self.format(data)
        src = edata.src
        source = xf.g1(data, source=None, src=None)
        method = xf.g1(data, mcall=0, method=0)
        #method = xf.g(data, method=0)
        info = xf.g(data, info=None)
        if info is not None:
            info = self.get_obj(info, src = edata.src, info = edata.info)
        einfo = edata.info
        if type(einfo)==dict and type(info) == dict:
            xf.fill(einfo, info, 1)
        if info is None:
            info = einfo
        if source is not None:
            source = conf.get_obj(source, info = info)
        if source is None:
            source = src
        if source is None:
            raise Exception(f"not object for method {method}")
        if src is None:
            src = source
        method = self.get_obj(method, conf, src)
        if type(method) in [str, bytes]:
            method = getattr(source, method)
        iargs, imaps = None, None
        ivars = None
        if type(info) == dict:
            iargs, imaps, ivars = xf.g(info, m_args = None, m_maps = None, vars=None)
        args = xf.g(data, args=[])
        maps = xf.g(data, maps ={})
        vars = xf.g(data, vars={})
        vars = {k:self.get_obj(v, conf, src) for k,v in vars.items()}
        if ivars is not None:
            xf.fill(ivars, vars, 1)
        ivars = vars
        if iargs is not None:
            args = iargs
        if imaps is not None:
            xf.fill(imaps, maps, 1)
        # args = [self.get_obj(v, conf, src, edata.info) for v in args]
        # maps = {k:self.get_obj(maps[k], conf, src, edata.info) for k in maps}
        self.push_vars(conf, ivars)
        args = [self.get_obj(v, conf, src) for v in args]
        maps = {k:self.get_obj(maps[k], conf, src) for k in maps}
        rst = method(*args, **maps)
        self.pop_vars(conf, ivars)
        return rst

pass
