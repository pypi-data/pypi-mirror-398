from .. import base
from .. import item
from .. import exp
class LRDeal(base.BaseDeal):
    """
        分隔符，有分隔符后将缓存的数据当作字符串
    """
    def init(self, left, right, name= "lr"):
        self.left = left
        self.right = right
        self.ll = len(left)
        self.lr = len(right)
        self.name = name
    def build(self, arr, l_item):
        # implement this
        return item.DealItem(arr, l_item.pos, self.id())
    def err(self, s):
        return s.replace("<lr>", self.name)
    def prev(self, buffer, queue, pos):
        cl = buffer.read(self.ll)
        cr = buffer.read(self.lr)
        if not self.same(self.left, cl) and not self.same(self.right, cr):
            return False
        if self.same(self.left, cl):
            buffer.pop_read(self.ll)
            rm = buffer.full()
            if len(rm.strip())>0:
                pos.update(rm)
                raise exp.FormatExp(self.err("unexcept char before <lr> left symbol"), pos.get(), rm)
            buffer.clean()
            pos.update(cl)
            queue.append(item.PrevItem(cl, pos.get(), self.id(), left = 1))
        else:
            buffer.pop_read(self.lr)
            rm = buffer.full()
            buffer.clean()
            pos.update(rm)
            # 这里对扩展不太好，需要注意
            #if len(rm.strip())>0 or len(queue)==0 or queue[-1].none(is_val = 1,type=self.id(), right=1,allow_empty=0):
            if len(rm.strip())>0:
                queue.append(item.PrevItem(rm, pos.get(), is_val=1))
            pos.update(cr)
            queue.append(item.PrevItem(cr, pos.get(), self.id(), right = 1))
        return True
    def deal(self, queue, stack):
        if len(queue)==0:
            return False
        _item = queue[0]
        if not _item.check(type=self.id()):
            return False
        if not _item.check(left=1) and not _item.check(right=1):
            return False
        queue.pop(0)
        if _item.check(left = 1):
            stack.append(_item)
            return True
        rst = []
        l_item = None
        while len(stack)>0:
            item_i = stack.pop(-1)
            if item_i.check(type = self.id()) and item_i.check(left=1):
                l_item = item_i
                break
            rst.append(item_i)
        if l_item is None:
            raise exp.FormatExp(self.err("find <lr> right symbal while not left symbal found"), _item.pos, _item.val)
        rst.reverse()
        rst = self.build(rst, l_item)
        stack.append(rst)
        return True

pass