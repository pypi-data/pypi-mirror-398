#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class ObjectVarDeal(FormatDeal):
    """
        对象变量ovar:
            {
                id:id
                type: ovar
                source: string
                ovar|key: string
                info: null
            }
        简写:
            [[ovar, id], source, key, info]
            [ovar, source, key]
        例:
            [ovar, obj.test, id] //返回对象id=obj.test的变量id
    """
    def init(self, fp_lists = None, fp_defaults = None):
        self.singles = {}
        self.sources = {}
        super().init("ObjectVarDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "ovar_lists.js"))
    def deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        conf = edata.conf
        data = self.format(data)
        src = edata.src
        source = xf.g1(data, source=None, src=None)
        #key = xf.g(data, key=0)
        key = xf.get_first(data, "ovar", "key", "data")
        info = xf.g(data, info=None)
        if info is not None:
            info = self.get_obj(info, src = edata.src, info = edata.info)
        else:
            info = edata.info
        if source is not None:
            source = conf.get_obj(source, info = info)
        if source is None:
            source = src
        if source is None:
            raise Exception(f"not object for key {key}")
        key = getattr(source, key)
        return key

pass
