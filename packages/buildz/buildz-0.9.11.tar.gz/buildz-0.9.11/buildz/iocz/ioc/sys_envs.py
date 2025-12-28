#
from .base import *
from .tdata import TagData
import os
class SysEnvs(Base):
    def init(self, ids):
        self.ids = ids
    def tget(self, key, ns=None, tag=None, id=None):
        rst = os.getenv(key)
        if rst is None and ns is not None:
            gkey = self.ids.id(self.ids(ns)+self.ids(key))
            rst = os.getenv(gkey)
        if rst is None:
            return None, TagData.Key.Pub, 0
        return rst, TagData.Key.Pub, 1