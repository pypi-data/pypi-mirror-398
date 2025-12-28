#coding=utf-8
from buildz import xf, pyz
from buildz.xf import g as xg
from buildz.base import Base as BzBase
import json
import builtins
typez = builtins.type
class IOCError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

pass
class IdNotFoundError(IOCError):
    pass
class Base(BzBase):
    def update_maps(self, maps, src, replace=1):
        xf.deep_update(maps, src, replace)
    def __init__(self, *args, **maps):
        self.init(*args, **maps)
    def init(self, *args, **maps):
        pass
    def __call__(self, *args, **maps):
        return self.deal(*args, **maps)
    def deal(self, *args, **maps):
        raise Exception("unexcept touch")
        return None

pass
class EncapeData(Base):
    def str(self):
        return f"EncapeData(data={self.data}, type = {self.type})"
    """
        包含data id对应的配置，配置文件id，配置文件对象
        [object.test, call, ]
    """
    def __init__(self, data, conf=None, local = False, type = None, src = None, info = None, confs = None, force_new = False):
        """
            data: 配置数据
            conf: 配置数据对应的配置文件的管理器
            local: 是否是locals的数据（配置文件局部数据）
            type: 配置数据的type字段
            src: 源对象，配置数据生成的对象调用conf获取对象，会有这个字段，目前只有object会放这个字段，其他要么透传要么不传
            info: 额外的调用信息，目前只有object会用到里面的id字段，作为单例额外输入
        """
        self.force_new = force_new
        if typez(data)==dict:
            pid = xf.g1(data, parent=None, template=None, temp=None)
            if pid is not None:
                data = dict(data)
                for pkey in "parent,temp,template".split(","):
                    if pkey in data:
                        del data[pkey]
                pids = pid
                if typez(pids)!=list:
                    pids = [pid]
                for pid in pids:
                    pedt = conf.get_data(pid, local=True, search_confs = True,src = src, info = info)
                    if pedt is None:
                        raise IOCError("unfind parend: "+pid)
                    pdt = pedt.data
                    if typez(pdt)!=dict:
                        raise IOCError("only dict can be a parent: "+pid)
                    self.update_maps(data, pdt, replace=0)
        self.data = data
        if conf is not None:
            self.sid = conf.id
            if type is None:
                type = conf.confs.get_data_type(data, 0, conf.default_type())
            if confs is None:
                confs = conf.confs
        else:
            self.sid = None
        self.src = src
        self.conf = conf
        self.confs = confs
        self.local = local
        self.type = type
        self.info = info
    def deal(self, remove = False):
        if self.conf is None:
            return self.confs.get(self, src = self.src, info=self.info, remove = remove, force_new = self.force_new)
        return self.conf.get(self, src = self.src, info=self.info, remove = remove, force_new = self.force_new)


pass
