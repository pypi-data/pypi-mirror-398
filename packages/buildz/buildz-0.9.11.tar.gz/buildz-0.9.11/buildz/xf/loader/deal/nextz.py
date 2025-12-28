from .. import base


class PrevNextDeal(base.BaseDeal):
    """
        读取下一个字符放缓存里，应放最低优先级
    """
    def prev(self, buffer, queue, pos):
        c = buffer.read(1,1)
        if c is None or len(c)==0:
            return False
        buffer.add(c)
        #pos.update(c)
        return True
    def deal(self, queue, stack):
        if len(queue)==0:
            return False
        obj = queue.pop(0)
        stack.append(obj)
        return True

pass