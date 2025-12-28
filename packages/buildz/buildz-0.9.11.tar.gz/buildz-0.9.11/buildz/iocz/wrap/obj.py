#

from .base import *
class ObjectItem(WrapItem):
    def call(self, cls):
        if self.add:
            self.conf['source'] = cls.__module__+"."+cls.__name__
        super().call(cls)
        return cls
class ObjectWrap(WrapBase):
    def call(self, **maps):
        return self.obj(**maps)
    def obj(self, **maps):
        maps['type'] = 'obj'
        return ObjectItem(self, maps, True, True)
    def s_args(self, s):
        list = self.loads(s)
        return self.args(*list)
    def args(self, *list):
        conf = {"args": self.loads_list(list)}
        return WrapItem(self, conf)
    def s_maps(self, s):
        maps = self.loads(s)
        return self.maps(**maps)
    def maps(self, **maps):
        conf = {"maps": self.loads_dict(maps)}
        return WrapItem(self, conf)
    def s_sets(self, s):
        sets = self.loads(s)
        return self.sets(**sets)
    def sets(self, **sets):
        conf = {"sets": self.loads_dict(sets)}
        return WrapItem(self, conf)