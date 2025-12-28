
from . import itemz
from ..readz import is_args
class Manager:
    def __init__(self):
        self.deals = []
    def add(self, fc):
        self.deals.append(fc)
    def deal(self, obj, conf):
        if obj.check(is_done=1):
            return obj
        for fc in self.deals:
            rst = fc(obj, conf)
            if rst is not None:
                return rst
        raise Exception("undealable type"+str(obj))
    def dump(self, obj, conf):
        stack_src = [[obj]]
        stack_build = [['root']]
        while len(stack_src)>0:
            crr = stack_src[-1]
            done = 1
            while len(crr)>0:
                obj = crr.pop(0)
                tobj = type(obj)
                if tobj == dict:
                    ncrr = []
                    for k in obj:
                        v = obj[k]
                        ncrr+=[k,v]
                    stack_src.append(ncrr)
                    stack_build.append(['dict'])
                    done = 0
                    break
                elif tobj in [list, tuple]:
                    ncrr = list(obj)
                    stack_src.append(ncrr)
                    stack_build.append(['list'])
                    done = 0
                    break
                elif is_args(obj):
                    ncrr = []
                    for k,v in obj.dicts.items():
                        ncrr+=[k,v]
                    ncrr = list(obj.lists)+ncrr
                    stack_src.append(ncrr)
                    stack_build.append([['args', len(obj.lists)]])
                    done = 0
                    break
                else:
                    stack_build[-1].append(itemz.ShowItem(obj, is_val=1))
            if done:
                stack_src.pop(-1)
                items = stack_build.pop(-1)
                rst = []
                for v in items[1:]:
                    v = self.deal(v, conf)
                    rst.append(v)
                if items[0] != 'root':
                    if type(items[0]) in (list, tuple) and items[0][0] == 'args':
                        obj = itemz.ShowItem(rst, is_args=1, list_num = items[0][1])
                    elif items[0] == 'list':
                        obj = itemz.ShowItem(rst, is_list=1)
                    else:
                        obj = itemz.ShowItem(rst, is_dict=1)
                    obj = self.deal(obj, conf)
                    stack_build[-1].append(obj)
                else:
                    stack_build.append(rst[0])
        return stack_build[0].val

pass