#coding=utf-8
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class JoinDeal(FormatDeal):
    """
    文件路径合并join:
        {
            id:id
            type: join
            data: [...]
        }
    简写:
        [[join, id], data]
        [join, data]
    例:
        [join, [[val, home], [val, buildz]]] //返回字符串 "home/buildz"
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("JoinDeal", fp_lists, fp_defaults, join(dp, "conf", "join_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        lists = xf.g1(data, join = [], data=[])
        conf = edata.conf
        rst = [self.get_obj(k, conf, edata.src, edata.info) for k in lists]
        return join(*rst)

pass
