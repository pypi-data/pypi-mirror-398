#
from ..ioc.base import Base, EncapeData
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class EnvDeal(FormatDeal):
    """
        环境变量env:
            {
                id: id
                type: env
                env|key: 环境变量key
                default: item_conf //可选
            }
        简写：
            [[id, env], key, default]
            [env, key, default]
            [env, key]
        例:
            [env, path] //读取环境变量path
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("EnvDeal", fp_lists, fp_defaults, join(dp, "conf", "env_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        key = xf.get_first(data, 'env', 'key')
        val = edata.conf.get_env(key)
        default = xf.g(data, default=None)
        if val is None and default is not None:
            val = self.get_obj(default, edata.conf)
        return val

pass
