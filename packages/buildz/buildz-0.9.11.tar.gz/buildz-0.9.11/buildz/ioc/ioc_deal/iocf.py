#coding=utf-8
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class IOCFObjectDeal(FormatDeal):
    """
        iocf字段ioc:
            {
                id:id
                type: iocf

                filepath: item_conf
                // or
                folder: item_conf
                pattern: item_conf
            }
        简写:
            [[ioc, id], filepath]
        例:
            [iocf, filepath] //
    """
    def init(self, fp_lists=None, fp_defaults=None):
        self.fps = set()
        self.ids = set()
        super().init("IOCFObjectDeal", fp_lists, fp_defaults, join(dp, "conf", "iocf_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        id = xf.g(data, id = None)
        data = self.fill(data)
        if id is not None:
            if id in self.ids:
                return None
            else:
                self.ids.add(id)
        fp = xf.g(data, filepath = None)
        fdir = xf.g(data, folder = None)
        pt = xf.g(data,  pattern = None)
        if fp is None:
            if fdir is None:
                raise Exception("filepath can't be null")
            else:
                fdir = self.get_obj(fdir, edata.conf)
                if pt is not None:
                    pt = self.get_obj(pt, edata.conf)
                fps = fz.search(fdir, pt)
        else:
            fp = self.get_obj(fp, edata.conf)
            fps = [fp]
        fps = [k for k in fps if k not in self.fps]
        if len(fps)==0:
            return None
        edata.conf.confs.add_fps(fps)
        self.fps.update(fps)
        return None

pass
