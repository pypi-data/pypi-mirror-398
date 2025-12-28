
'''
数据封装类
val是数据（字符）值
pos是字符在文件里的位置(第几行第几列)
remain和type？
'''
class ShowItem:
    def __str__(self):
        return "<show_item val={val}, deep = {deep}, maps={maps}>".format(val = str(self.val), maps=self._maps, deep = self.deep)
    def __repr__(self):
        return str(self)
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
    def __init__(self, val, deep=1,  **maps):
        self.val= val
        self._maps = maps
        self.deep = deep

pass