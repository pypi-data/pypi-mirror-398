
'''
数据封装类
val是数据（字符）值
pos是字符在文件里的位置(第几行第几列)
remain和type？
'''
class PrevItem:
    def __str__(self):
        return "<prev_item val={val}, type = {type}, pos = {pos}, maps={maps}>".format(val = str(self.val), type = str(self.type), pos = str(self.pos), maps=self._maps)
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
    def __init__(self, val, pos, type = None, remain=None, **maps):
        self.val= val
        self.pos= pos
        self.remain= remain
        self._maps = maps
        self.type = type

pass
class DealItem(PrevItem):
    def __str__(self):
        return "<deal_item val={val}, type = {type}, pos = {pos}, maps={maps}>".format(val = str(self.val), type = str(self.type), pos = str(self.pos), maps=self._maps)

