#coding=utf-8
from ..ioc.base import Base, EncapeData, IdNotFoundError
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
import re
class RefsDeal(FormatDeal):
    """
        引用refs，返回的是一个列表，长度可能为0:
            {
                id: id
                type: refs
                refs|key: 引导数据id正则匹配表达式
                info: item_conf, 额外的引用信息, 默认null
            }
        简写:
            [[refs, id], [key, force_new], info]
            [[refs, id], key, info]
        极简:
            [refs, key]
        例:
            [refs, r".*obj\.test.*"] // 数据项"obj.test"的引用
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("RefsDeal", fp_lists, fp_defaults, join(dp, "conf", "refs_lists.js"), None)
    def match(self, key, pt):
        rst = len(re.findall(pt, key))>0
        # if rst:
        #     print(f"[TESTZ] refs match: {key} in {pt}")
        # else:
        #     print(f"[TESTZ] refs NOT match: {key} in {pt}")
        return rst
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        pt = xf.get_first(data, 'refs', 'key')
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
        vars = edata.conf.var_keys()
        vars = [key for key in vars if self.match(key, pt)]
        rst = [edata.conf.get_var(key)[0] for key in vars]
        ids = edata.confs.full_ids(edata.conf)
        ids = [obj for obj in ids if self.match(obj[0], pt) or self.match(obj[1], pt)]
        objs = []
        for obj in ids:
            #print(f"[TESTZ] REFS get: {obj[2]}.get({obj[1]}, src={edata.src})")
            _obj = obj[2].get(obj[1], info = info, src = edata.src)
            objs.append(_obj)
        #objs = [obj[2].get(obj[1], info = info, src = edata.src) for obj in ids]
        rst+=objs
        return rst

pass
