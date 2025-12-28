from .. import base
from .. import item

class PrevNextDeal(base.BaseDeal):
    def labels(self):
        return ['']
    #def types(self):
    #    return [""]
    """
        读取下一个字符放缓存里，应放最低优先级
    """
    def deal(self, buffer, arr, mg):
        c = buffer.read_cache(1)
        if len(c)==0:
            rm = buffer.full().strip()
            buffer.clean()
            if len(rm)==0:
                return False
            obj = item.Item(rm, type = 'str', is_val = 0)
            arr.append(obj)
            # TODO return True?
            return False
        return True

pass