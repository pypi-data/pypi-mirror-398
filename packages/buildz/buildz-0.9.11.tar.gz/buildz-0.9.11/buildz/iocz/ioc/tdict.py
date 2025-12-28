#
from ... import pyz,dz,Base
class TagDict(Base):
    def remove(self, key, tag=None):
        tag = pyz.nnull(tag, self.default)
        rst = dz.get_set(self.maps, tag, dict())
        dz.dremove(rst, key)
    def update(self, maps, tag=None):
        tag = pyz.nnull(tag, self.default)
        rst = dz.get_set(self.maps, tag, dict())
        dz.fill(maps, rst)
    def set(self, key, val, tag=None):
        tag = pyz.nnull(tag, self.default)
        rst = dz.get_set(self.maps, tag, dict())
        dz.dset(rst, key, val)
    def get(self, key, tags=None):
        if tags is None:
            tags = self.maps.keys()
        elif type(tags) not in (list,tuple,set):
            tags = [tags]
        for tag in tags:
            if tag not in self.maps:
                continue
            rst = self.maps[tag]
            val, has = dz.dget(rst, key)
            if has:
                return val, tag, 1
        return None, None, 0
    def tag(self, tag):
        rst = dz.get_set(self.maps, tag, dict())
        return rst
    def __getattr__(self, tag):
        return self.tag(tag)
    def init(self, default=""):
        self.maps = {}
        self.default=default

pass