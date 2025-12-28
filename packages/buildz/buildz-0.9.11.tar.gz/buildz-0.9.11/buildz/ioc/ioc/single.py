#coding=utf-8
from .base import Base, EncapeData,IOCError
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join

class Single(Base):
    """
        virtual deal
        {
            single=1/0
            info: {
                cid: ??
            }
        }
    """
    def init(self, single="single", cid = "id", default=1):
        self.k_cid = cid
        self.k_single = single
        self.default = default
        self.singles = {}
    def get_ids(self, edata: EncapeData):
        if edata.force_new:
            return None
        sid = edata.sid
        data = edata.data
        info = edata.info
        if type(info) == dict:
            cid = xf.get(info, self.k_cid, None)
        else:
            cid = None
        id = xf.g(data, id = None)
        single = xf.get(data, self.k_single, None)
        if id is None:
            single = 0
        if single is None:
            single = self.default
        ids = None
        if single or cid is not None:
            if cid is not None:
                ids = [sid, 'local_id', id, cid]
            else:
                ids = [sid, 'single', id]
        return ids
    def get_by_ids(self, ids):
        if ids is None:
            return None
        obj = xf.gets(self.singles, ids)
        return obj
    def get(self, edata:EncapeData):
        ids = self.get_ids(edata)
        return self.get_by_ids(ids)
    def set_by_ids(self, ids, obj):
        if ids is None:
            return
        xf.sets(self.singles, ids, obj)
    def set(self, edata:EncapeData, obj):
        if not isinstance(edata, EncapeData) and isinstance(obj, EncapeData):
            edata, obj = obj, edata
        ids = self.get_ids(edata)
        self.set_by_ids(ids, obj)
    def rm_by_ids(self, idsj):
        if ids is None:
            return
        xf.removes(self.singles, ids)
    def remove(self,edata:EncapeData):
        ids = self.get_ids(edata)
        self.rm_by_ids(ids)

pass
