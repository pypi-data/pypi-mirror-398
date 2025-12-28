#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class CallsDeal(FormatDeal):
    """
    函数调用序列calls:
        {
            id:id
            type:calls
            calls: [
                item_conf,
                ...
            ]
        }
    简写:
        [[calls, id], calls]
        [calls, calls]
    例:
        //顺序调用buildz.pyz.pyexe()和buildz.pyz.pypkg()
        [[main_call, calls], [[call, buildz.pyz.pyexe], [call, buildz.pyz.pypkg]]] 
    """
    def init(self, fp_lists = None, fp_defaults = None):
        super().init("CallsDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "calls_lists.js"),
            join(dp, "conf", "calls_defaults.js"))
    def deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        conf = edata.conf
        data = self.format(data)
        src = edata.src
        info = edata.info
        calls = xf.g1(data, calls=[], data = [])
        rst = None
        for call in calls:
            rst = self.get_obj(call, conf, src, info=info)
        return rst

pass
