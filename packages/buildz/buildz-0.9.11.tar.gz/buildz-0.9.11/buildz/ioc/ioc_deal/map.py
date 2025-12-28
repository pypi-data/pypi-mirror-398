#coding=utf-8
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class MapDeal(FormatDeal):
    """
    map:
        {
            id:id
            type:map
            map|data: {
                key1: item_conf,
                ...
            }
        }
    简写:
        [[map, id], data]
        [map, data]
    例:
        [map, {obj:[ref, obj.test], path: [env, path]}] // 返回{obj:对对象obj.test的索引, path: 环境变量path的值}
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("MapDeal", fp_lists, fp_defaults, join(dp, "conf", "map_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        conf = edata.conf
        data = self.fill(data)
        maps = xf.g1(data, map = {}, data={})
        rst = {k:self.get_obj(maps[k], conf, edata.src, edata.info) for k in maps}
        return rst

pass
