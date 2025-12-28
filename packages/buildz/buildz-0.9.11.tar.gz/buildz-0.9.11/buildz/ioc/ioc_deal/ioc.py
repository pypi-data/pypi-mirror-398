#coding=utf-8
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class IOCObjectDeal(FormatDeal):
    """
        ioc字段ioc:
            {
                id:id
                type: ioc
                //default conf
                key: string = conf, confs, sid 
            }
        简写:
            [[ioc, id], key]
            [ioc]
        例:
            [ioc, conf] //返回ioc内部数据的conf字段
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("IOCObjectDeal", fp_lists, fp_defaults, join(dp, "conf", "ioc_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        key = xf.get_first(data, 'ioc', 'key')
        if not hasattr(edata, key):
            return None
        return getattr(edata, key)

pass
