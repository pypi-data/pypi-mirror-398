#

from .middle_base import MiddleBase
import torch
from buildz import logz
log = logz.simple("middle_cache.log")("GPUZ_CACHE")
log.show("debug", 0)
class MiddleCache(MiddleBase):
    '''
        nets: 模型列表
        win_size: gpu设备可存放的模型数量
        deal_after_backup: fc(model) 或 None, 在模型进行backward后调用
        cal_dv: 计算设备，默认cuda
        cache_dv: 缓存设备，默认cpu
        fc_inputs_to: fc(inputs, dv) 或 None, 需要把输入参数转换成设备dv对应的数据时候使用，默认输入参数是Tensor的tuple或者就是Tensor
        cal_nets: 模型列表，nets中的一部分，不进行两个设备转换，而是一直放在cal_dv上的模型
        cache_nets: 模型列表，nets中的一部分，不进行两个设备转换，而是一直放在cache_dv上的模型
        preload: 预加载，把模型加载到计算设备时，把后面的模型也加载到计算设备上（已经加载到计算设备上的放缓存设备中）
    '''
    def init(self, nets, win_size=1, deal_after_backup=None, cal_dv='cuda', cache_dv='cpu', fc_inputs_to = None, cal_nets = [], cache_nets = [], preload = False):
        cache_dv = torch.device(cache_dv) if type(cache_dv)==str else cache_dv
        cal_dv = torch.device(cal_dv) if type(cal_dv)==str else cal_dv
        [net.to(cache_dv) for net in cache_nets]
        [net.to(cal_dv) for net in cal_nets]
        self.src = nets
        static_dv = {}
        static_dv.update({id(net):cache_dv for net in cache_nets})
        static_dv.update({id(net):cal_dv for net in cal_nets})
        self.static_dv = static_dv
        self.nets = {id(net):net for net in nets if id(net) not in self.static_dv}
        # TEST CODE
        # self.indexes = {}
        # for i in range(len(nets)):
        #     self.indexes[id(nets[i])] = i
        # DONE
        self.cache_dv = cache_dv
        self.cal_dv = cal_dv
        self.hook(nets)
        # 
        self.datas = {id(net):[] for net in nets}
        self.cal_ids = []
        self.deal_after_backup = deal_after_backup
        if fc_inputs_to is None:
            fc_inputs_to = self.list_inputs_to
        self.inputs_to = fc_inputs_to
        self.nexts = {}
        self.prevs = {}
        self.curr = -1
        #self.caches = set()
        self.mark_static = None
        self.win_size = win_size
        self.preload = preload
    def train(self):
        [net.train() for net in self.src]
    def eval(self):
        [net.eval() for net in self.src]
    @staticmethod
    def list_inputs_to(datas, dv):
        if isinstance(datas, torch.Tensor):
            return datas.to(dv)
        # assert datas is not None, "inputs datas is null"
        inputs = tuple([k.to(dv) for k in datas])
        return inputs
    @staticmethod
    def deep_inputs_to(datas, dv):
        '''
            数据比较复杂用这个，会递归搜索list，tuple和dict病做转换
        '''
        log.debug(f"deep_inputs_to")
        if isinstance(datas, torch.Tensor):
            return datas.to(dv)
        if type(datas) in (list, tuple):
            rst = [MiddleCache.deep_inputs_to(k, dv) for k in datas]
            if type(datas)==tuple:
                rst = tuple(rst)
            return rst
        if type(datas) == dict:
            rst = {k:MiddleCache.deep_inputs_to(v, dv) for k,v in datas.items()}
            return rst
        assert 0, f"undealable datas type: {type(datas)}"
    def before_forward(self):
        log.debug(f"before_forward")
        self.curr = -1
        #self.caches = set()
        for mid in self.datas:
            self.datas[mid] = []
    def after_forward(self):
        pass
    def before_backward(self):
        log.debug(f"before_backward")
        self.curr = -1
    def backupable(self, model):
        mid = id(model)
        return mid in self.cal_ids or mid in self.static_dv
        #return mid not in self.caches
    def after_backward(self):
        pass
    def to_dv(self, mid, dv):
        self.nets[mid].to(dv)
        self.datas[mid] = [self.inputs_to(k, dv) if k is not None else k for k in self.datas[mid]]
    def to_cal(self, mid, pop = 0):
        log.debug(f"to_cal")
        if mid in self.cal_ids:
            return 0
        if len(self.cal_ids)>=self.win_size:
            xid = self.cal_ids.pop(pop)
            #print(f"model_{self.indexes[xid]} to CPU device")
            self.to_dv(xid, self.cache_dv)
            #self.caches.add(xid)
        #print(f"model_{self.indexes[mid]} to CUDA device")
        self.to_dv(mid, self.cal_dv)
        # if mid in self.caches:
        #     self.caches.remove(mid)
        if pop==-1:
            self.cal_ids = [mid]+self.cal_ids
        else:
            self.cal_ids.append(mid)
        return 1
    def hook_forward_before(self, model, ins):
        mid = id(model)
        log.debug(f"hook_forward_before", model, id(model))
        self.mark_static = mid in self.static_dv
        if self.mark_static:
            # assert ins is not None, "hook_forward_before A"
            return self.inputs_to(ins, self.static_dv[mid])
        prev = self.curr
        if prev >= 0:
            self.nexts[prev] = mid
            if mid not in self.prevs:
                self.prevs[mid] = prev
        self.curr = mid
        self.loop_to_cal(mid, 0, self.nexts)
        # assert ins is not None, "hook_forward_before B"
        return self.inputs_to(ins, self.cal_dv)
    def hook_forward_after(self, model):
        log.debug(f"hook_forward_after", model, id(model))
        pass
    def hook_backward_after(self, model):
        log.debug(f"hook_backward_after", model, id(model))
        #print(f"hook_backward_after", model, id(model))
        assert self.backupable(model)
        mid = id(model)
        if self.deal_after_backup is not None:
            self.deal_after_backup(model)
        if id in self.static_dv:
            return
        after = self.curr
        if after>=0:
            self.prevs[after] = mid
        self.curr = mid
    def tensor_save(self, tuple_data):
        log.debug(f"tensor_save")
        if self.mark_static:
            return -1, tuple_data
        index = len(self.datas[self.curr])
        self.datas[self.curr].append(tuple_data)
        log.debug(f"done tensor_save", self.curr, index)
        return self.curr, index
    def tensor_load(self, obj):
        log.debug(f"tensor_load", obj)
        if obj[0]<0:
            return obj[1]
        curr, index = obj
        self.loop_to_cal(curr, -1, self.prevs)
        tuple_data = self.datas[curr][index]
        # assert tuple_data is not None
        self.datas[curr][index] = None
        return tuple_data
    def loop_to_cal(self, mid, pop, nexts):
        log.debug(f"loop_to_cal")
        if mid in self.cal_ids:
            return
        self.to_cal(mid, pop)
        if not self.preload:
            return
        count = 1
        while count<self.win_size and mid in nexts:
            mid = nexts[mid]
            if mid in self.cal_ids:
                break
            self.to_cal(mid, pop)
            count+=1
            
pass