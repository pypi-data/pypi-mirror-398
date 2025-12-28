#coding=utf-8
from ..ioc.base import Base, EncapeData, IdNotFoundError
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class RefDeal(FormatDeal):
    """
        引用ref:
            {
                id: id
                type: ref
                ref|key: 引导数据id
                default: 默认值
                info: item_conf, 额外的引用信息, 默认null
                force_new: 无视single配置创建新实例，默认false
            }
        简写:
            [[ref, id], [key, force_new], default, info]
            [[ref, id], key, default, info]
        极简:
            [ref, key]
        例:
            [ref, obj.test] // 数据项"obj.test"的引用
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("RefDeal", fp_lists, fp_defaults, join(dp, "conf", "ref_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        key = xf.get_first(data, 'ref', 'key')
        key = self.get_obj(key, edata.conf, src = edata.src)
        info = xf.g(data, info=None)
        if info is not None and type(info)==dict:
            #info = {k:self.get_obj(info, edata.conf, src = edata.src) for k in info}
            info = {'type':'map', 'data':info}
            info = self.get_obj(info, edata.conf, src = edata.src)
        else:
            info = {}
        _info = edata.info
        if type(_info)==dict:
            xf.deep_update(info, _info, 1)
        var, exist = edata.conf.get_var(key)
        if exist:
            return var
        try:
            return edata.conf.get_obj(key, info = info, src = edata.src)
        except IdNotFoundError as exp:
            #print(f"[testz] ref data: {data} in {edata.conf}")
            if "default" in data:
                key = data['default']
                return self.get_obj(key, edata.conf, src=edata.src)
            raise exp

pass
