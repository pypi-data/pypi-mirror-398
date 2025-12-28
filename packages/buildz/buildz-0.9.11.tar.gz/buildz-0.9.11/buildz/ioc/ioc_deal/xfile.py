#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class XfileDeal(FormatDeal):
    """
    配置文件载入xfile/xf:
        {
            id:id
            type:xfile
            filepath: item_conf(fp) 
            # or fp: item_conf(fp)
        }
    简写:
        [[xfile, id], fp]
        [xfile, fp]
        [xf, fp]
    例:
        [xfile, test.js]
        [xfile, [val, test.js]]
    """
    def init(self, fp_lists = None, fp_defaults = None):
        self.singles = {}
        self.sources = {}
        super().init("XfileDeal", fp_lists, fp_defaults, 
            join(dp, "conf", "xfile_lists.js"),
            join(dp, "conf", "xfile_defaults.js"))
    def deal(self, edata:EncapeData):
        sid = edata.sid
        data = edata.data
        conf = edata.conf
        data = self.format(data)
        fp = xf.g(data, filepath=None)
        if fp is None:
            fp = xf.g(data, fp = fp)
        fp = self.get_obj(fp, conf)
        rst = xf.loads(xf.fread(fp))
        return rst

pass
