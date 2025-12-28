from .. import base


class PrevSpcDeal(base.BaseDeal):
    def has_prev(self):
        return 1
    def has_deal(self):
        return 0
    """
        去掉左空格
    """
    def prev(self, buffer, queue, pos):
        if buffer.size()>0:
            return False
        c = buffer.read()
        if len(c)==0:
            return False
        if len(c.strip())==0:
            buffer.pop_read()
            buffer.clean()
            return True
        return False

pass