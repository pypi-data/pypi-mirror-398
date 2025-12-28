from .. import base
from .. import item

class PrevSptDeal(base.BaseDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, spt, allow_empty = False):
        self.spt = spt
        self.allow_empty = allow_empty
        self.l = len(spt)
    def prev(self, buffer, queue, pos):
        c = buffer.read(self.l)
        if not self.same(c, self.spt):
            return False
        buffer.pop_read(self.l)
        data = buffer.full()
        buffer.clean()
        crr = pos.get()
        pos.update(data)
        item_spt = item.PrevItem(self.spt, pos.get(), self.id(), src='spt', allow_empty = self.allow_empty)
        pos.update(c)
        data = data.strip()
        if len(data)==0 and not self.allow_empty:
            queue.append(item_spt)
            return True
        if len(data)==0:
            if len(queue)>0 and queue[-1].any(is_val = 1, right=1):
                queue.append(item_spt)
                return True
        obj = item.PrevItem(data, crr, is_val = 1, src='spt')
        queue.append(obj)
        queue.append(item_spt)
        return True
    def deal(self, queue, stack):
        bl = False
        while len(queue)>0 and queue[0].check(type = self.id()):
            queue.pop(0)
            bl = True
        return bl

pass