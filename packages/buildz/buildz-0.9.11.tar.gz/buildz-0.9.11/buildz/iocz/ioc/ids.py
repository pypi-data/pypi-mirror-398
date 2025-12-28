from .base import Base
class Ids(Base):
    '''
    '''
    def init(self, spt):
        self.spt = spt
    def id(self, *ids):
        if len(ids)==0:
            return None
        elif len(ids)==1:
            if type(ids[0]) in (list, tuple):
                ids = ids[0]
        return self.spt.join(ids)
    def ids(self, id):
        if id is None:
            return []
        if type(id) in (list, tuple):
            return id
        return id.split(self.spt)
    def call(self, id):
        return self.ids(id)
pass

