#
'''
model.register_forward_pre_hook 会在模型forward之前调用
model.register_forward_hook 会在模型forward之后调用

-------------
之前写的不准确的：
model.register_full_backward_hook 会在模型反向梯度计算之后调用，注，模型列表第一个模型会在计算梯度前调用，该hook参数是(model, grad_ins, grad_outs),model是当前模型，grad_outs是后面的模型传来的，grad_ins是grad_outs经过该model计算后往前传的梯度，好像是第一个模型因为不用往前传梯度，提前调用了

修改后：
model.register_full_backward_hook 会在模型反向梯度计算之后调用，注，当前模型如果不需要再往前传送梯度，会在反向梯度计算前调用该方法，该hook参数是(model, grad_ins, grad_outs),model是当前模型，grad_outs是后面的模型传来的，grad_ins是grad_outs经过该model计算后往前传的梯度

导致的后果是调用该方法的时候，计算数据还没存到显卡，需要延后调用
-------------


torch.autograd.graph.saved_tensors_hooks(hook_pack, hook_unpack):
    hook_pack会在Tensor计算完成后把之后反向梯度计算要用的tensor进行存储
    hook_unpack是在Tensor反向梯度计算前取回之前存储的tensor，注：调用loss.backward不用在with ...saved_tensors_hooks(..)中
'''

import torch
from ... import Base
from ... import pyz
class MiddleBase(Base):
    def init(self, nets):
        self.hook(nets)
    def before_forward(self):
        pass
    def after_forward(self):
        pass
    def before_backward(self):
        pass
    def after_backward(self):
        pass
    def hook_forward_before(self, model, ins):
        return ins.cpu()
    def hook_forward_after(self, model):
        pass
    def hook_backward_after(self, model):
        pass
    def tensor_save(self, tuple_data):
        obj = tuple_data
        return obj
    def tensor_load(self, obj):
        tuple_data = obj
        return tuple_data
    # 下面是不应修改的部分
    def hook(self, nets):
        net = nets[0]
        # self.start_id = id(net)
        # self.start_net = net
        hooks = []
        hooks += [net.register_forward_pre_hook(self.hook_forward_before) for net in nets]
        hooks+=[net.register_forward_hook(self.native_hook_forward_after) for net in nets]
        if hasattr(nets[0], "register_full_backward_hook"):
            hooks+=[net.register_full_backward_hook(self.native_hook_backward_after) for net in nets]
        else:
            hooks+=[net.register_backward_hook(self.native_hook_backward_after) for net in nets]
        self.hooks = hooks
        self.wait_backup_models = []
    def unhook(self):
        [hook.remove() for hook in self.hooks]
    def do_forward(self, fc):
        with self.wrap_forward():
            return fc()
    def do_backward(self, fc):
        with self.wrap_backward():
            return fc()
    def backupable(self, model):
        return True
    def wrap_backward(self):
        def wrap_enter():
            self.wait_backup_models = []
            self.before_backward()
        def wrap_out(exc_type, exc_val, exc_tb):
            #self.hook_backward_after(self.start_net)
            #print(f"BACK OUT MODELS:", self.wait_backup_models)
            for model in self.wait_backup_models:
                self.hook_backward_after(model)
            self.after_backward()
        return pyz.With(wrap_enter, wrap_out, True)
    def wrap_forward(self):
        obj = torch.autograd.graph.saved_tensors_hooks(self.tensor_save, self.tensor_load)
        def wrap_enter():
            self.before_forward()
            obj.__enter__()
        def wrap_out(exc_type, exc_val, exc_tb):
            obj.__exit__(exc_type, exc_val, exc_tb)
            self.after_forward()
        return pyz.With(wrap_enter, wrap_out, True)
    def native_hook_backward_after(self, model, grad_up, grad_src):
        # if id(model)==self.start_id:
        #     return
        if not self.backupable(model):
            self.wait_backup_models.append(model)
            return
        self.hook_backward_after(model)
    def native_hook_forward_after(self, model, ins, outs):
        self.hook_forward_after(model)
pass