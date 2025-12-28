
class Conf:
    def none(self, **maps):
        for k in maps:
            v = maps[k]
            if self.maps(k)==v:
                return False
        return True
    def any(self, **maps):
        for k in maps:
            v = maps[k]
            if self.maps(k)==v:
                return True
        return False
    def check(self, **maps):
        for k in maps:
            v = maps[k]
            if self.maps(k)!=v:
                return False
        return True
    def maps(self, key):
        if key not in self._maps:
            if key == 'type':
                return self.type
            return None
        return self._maps[key]
    def set(self, **maps):
        for k in maps:
            v = maps[k]
            self._maps[k] = v
    def get(self, **maps):
        rst = []
        for k in maps:
            df = maps[k]
            v = self.maps(k)
            if v is None:
                v = df
            rst.append(v)
        if len(rst)==1:
            rst = rst[0]
        return rst
    def __init__(self, *argv, **maps):
        self.init(*argv, **maps)
    def init(self, **maps):
        self._maps = maps
    def s(self, val):
        #print("bytes:", self.get(bytes=0))
        if self.get(bytes=0):
            if type(val)==str:
                val = val.encode(self.get(code="utf-8"))
        else:
            if type(val)==bytes:
                val = val.decode(self.get(code="utf-8"))
        return val

pass