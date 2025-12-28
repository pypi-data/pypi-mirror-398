#
from ..ioc.base import Base, EncapeData

class DealDemo(Base):
    def init(self):
        pass
    def deal(self, edata:EncapeData):
        data = edata.data
        src = edata.src
        conf = edata.conf
        sid = edata.sid
        confs = edata.confs
        return {'type': edata.type, 'id': confs.get_data_id(data), 'conf': sid}

pass
