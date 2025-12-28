#
from ..ioc.base import Base, EncapeData,IOCError
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class BranchDeal(FormatDeal):
    """
        分支branch:
            {
                id: id
                type: branch
                judge: item_conf
                vals: {
                    judge_val: item_conf
                    ...
                }
                default(optional): item_conf
            }
        简写：
            [[branch, id], judge, {vals}, default]
            [branch, judge, {vals}, default]
            [branch, judge, {vals}]
        例:
            [branch, [env, env.test], {true:..., false: ...}]
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("BranchDeal", fp_lists, fp_defaults, join(dp, "conf", "branch_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        judge = xf.get_first(data, 'judge', 'key', 'var')
        judge = self.get_obj(judge, edata.conf, edata.src, edata.info)
        vals = xf.get_first(data, 'vals', 'data', 'datas')
        val = None
        if judge in vals:
            val = vals[judge]
            val = self.get_obj(val, edata.conf, edata.src, edata.info)
            return val
        if 'default' not in data:
            raise IOCError(f"<branch> not any vals match '{judeg}'")
        default = data['default']
        val = self.get_obj(default, edata.conf, edata.src, edata.info)
        return val

pass
