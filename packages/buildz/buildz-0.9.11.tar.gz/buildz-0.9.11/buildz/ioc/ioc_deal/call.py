#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class CallDeal(FormatDeal):
    """
    函数调用call:
        {
            id:id
            type:call
            call|method: import路径+"."+方法名
            vars: [...]
            args: [item_conf, ...]
            maps: {
                key1:item_conf,
                ...
            }
        }
    简写:
        [[call, id], method, args, maps]
        [call, method]
    例:
        [call, buildz.ioc.demo.test.test] //调用buildz.ioc.demo.test下的test方法
    """
    def init(self, fp_lists = None, fp_defaults = None):
        self.singles = {}
        self.sources = {}
        super().init("CallDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "call_lists.js"),
            join(dp, "conf", "call_defaults.js"))
    def deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        conf = edata.conf
        data = self.format(data)
        src = edata.src
        method = xf.g1(data, call=0, method=0)
        #method = xf.g(data, method=0)
        method = self.get_obj(method, conf, src)
        if type(method) in [str, bytes]:
            method = pyz.load(method)
        info = edata.info
        iargs, imaps = None, None
        ivars = None
        if type(info) == dict:
            iargs, imaps,ivars = xf.g(info, args = None, maps = None, vars=None)
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
        # args = [self.get_obj(v, conf, src, info = edata.info) for v in args]
        # maps = {k:self.get_obj(maps[k], conf, src, info = edata.info) for k in maps}
        self.push_vars(conf, ivars)
        args = [self.get_obj(v, conf, src) for v in args]
        maps = {k:self.get_obj(maps[k], conf, src) for k in maps}
        rst = method(*args, **maps)
        self.pop_vars(conf, ivars)
        return rst

pass
