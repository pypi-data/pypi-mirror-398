#coding=utf-8
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class ListDeal(FormatDeal):
    """
        list:
            {
                id: id
                type: list
                data: [
                    item_conf,
                    ...
                ]
            }
        简写:
            [[list, id], data]
            [list, data]
        例:
            [list, [[ref, obj.test], [env, path]]] // 返回列表,第0个元素是对数据obj.test的索引，第二个是环境变量path的值
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("ListDeal", fp_lists, fp_defaults, join(dp, "conf", "list_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        lists = xf.g1(data, list = [], data=[])
        conf = edata.conf
        rst = [self.get_obj(k, conf, edata.src, edata.info) for k in lists]
        return rst

pass
