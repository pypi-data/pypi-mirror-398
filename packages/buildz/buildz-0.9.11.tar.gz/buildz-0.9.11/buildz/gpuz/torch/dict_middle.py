#
import torch
from torch import nn
import threading as th
from ... import Base
import numpy as np
class Fcs(Base):
    def init(self, fcs):
        self.fcs = fcs
    def __getattr__(self, key):
        def fc(*a,**b):
            return [getattr(fc, key)(*a,**b) for fc in self.fcs]
        return fc

pass
class DictCache(Base):
    '''
        用处：显存不够的时候，可以用本代码框架，代码会在forward和backward的时候自动把nets列表里需要计算的模型放入显存，不需要计算的放到内存，需要进行卷积训练的时候用处比较大（卷积计算显卡比CPU强太多）
        暂不支持多显卡，因为开发者的电脑没有多显卡
        DictCache实际提供两个功能：
            1，缓存功能：模型需要使用的时候放显存，不需要的时候放内存
            2，部分模型全放显存，部分模型全放内存，DictCache内部做传入数据的显存和内存的转换
            两个功能可以同时使用，即部分模型用的时候放显存，不用的时候放内存，部分模型全放显存，部分模型全放内存
        使用本框架需要使用者手动把模型拆成多个小模型，把小模型列表nets传入DictCache
        训练时大概有纯显卡二分之一到三分之一的性能，起码比CPU好，尤其是进行卷积计算，比cpu好太多
        训练完使用时的线性层则比CPU还慢，感觉没必要用，不过DictCache也提供了部分模型全放显存，部分模型全放内存的功能，显存不够的时候可以使用
        DictCache里的Dict意思是传入的模型列表nets会存字典里，Cache就是用内存作为显存的缓存
        代码实现原理是利用pytorch的几个勾子函数：
            model.register_forward_pre_hook会在模型forward之前调用
            model.register_forward_hook会在模型forward之后调用
            model.register_full_backward_hook会在模型反向梯度计算之后调用
            torch.autograd.graph.saved_tensors_hooks(hook_pack, hook_unpack):
                hook_pack会在模型forward的时候把之后反向梯度计算要用的tensor进行存储
                hook_unpack是在反向梯度计算的时候取回forward存储的tensor
        代码例子:
        code in buildz.gpuz.test.demo:

            from buildz.gpuz.torch import DictCache
            import torch
            from torch import nn,optim
            from torch.utils.data import DataLoader, Dataset
            class TestDataset(Dataset):
                def __init__(self, num, dims):
                    self.num = num
                    self.dims = dims
                    self.datas = torch.rand(num, dims)
                    self.targets = torch.rand(num, dims)
                def __len__(self):
                    return self.num
                def __getitem__(self, i):
                    return self.datas[i], self.targets[i]
            dims = 12
            dataset = TestDataset(30, dims)
            dataloader = DataLoader(dataset, 10)
            class MiniModel(nn.Module):
                def __init__(self, dims, mdims, num):
                    super().__init__()
                    nets = [nn.Linear(dims, mdims)]
                    nets += [nn.Linear(mdims,mdims) for i in range(num)]
                    nets.append(nn.Linear(mdims,dims))
                    self.nets = nn.Sequential(*nets)
                def forward(self, inputs):
                    return self.nets(inputs)
            models = [MiniModel(dims, 32, 3) for i in range(10)]
            opts = [optim.Adam(model.parameters(), lr=0.001) for model in models]
            #可以指定哪些模型全部放cuda或者全部放cpu
            cuda_models = [models[1],models[2]]
            cpu_models = [models[-1]]
            real_model = nn.Sequential(*models)
            loss_fn = torch.nn.MSELoss()
            def opt_step(net, opt):
                # 如果模型只是用来测试，不做训练，可以不传该函数，同时opts传入空就可以
                # 对模型的一些其他优化，可以写可以不写，主要是调用opt.step()进行当前小模型的模型训练
                # 另外，opt不一定就是优化函数，可以是任何数据，其只取决于创建DictCache的时候传入的opts是什么
                torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
                opt.step()
            cache = DictCache([torch.device('cuda'), torch.device('cpu')],models,opts,3,opt_step, [cuda_models,cpu_models])

            # 训练:
            [md.train() for md in models]
            for inputs,targets in dataloader:
                inputs,targets = inputs.cuda(),targets.cuda()
                [opt.zero_grad() for opt in opts]
                outs = cache.do_forward(lambda:real_model(inputs))
                loss = loss_fn(outs, targets)
                cache.do_backward(lambda: loss.backward())
                # opt.step()在do_backward里会自动调用
                print(loss.item())
            # 测试:
            inputs = torch.rand(1, dims).cuda()
            with torch.no_grad():
                outputs = cache.do_forward(lambda:real_model(inputs))
            print(outputs)
            
            # 对比不用DictCache的时候
            # 注意：模型放入DictCache之后会挂上勾子函数，不再用DictCache的时要先调用DictCache的remove方法
            cache.remove()
            full_opt = optim.Adam(real_model.parameters(), lr=0.001)
            # 训练:
            real_model.cuda()
            real_model.train()
            for inputs,targets in dataloader:
                inputs,targets = inputs.cuda(),targets.cuda()
                full_opt.zero_grad()
                outs = real_model(inputs)
                loss = loss_fn(outs, targets)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(real_model.parameters(), max_norm=1.0)
                full_opt.step()
                print(loss.item())
            # 测试:
            inputs = torch.rand(1, dims).cuda()
            with torch.no_grad():
                outputs = real_model(inputs)
            print(outputs)
    '''
    def init(self, dvs, nets, opts=None, win_size=1, backward_deal=None, dvs_nets=None, fc_inputs_to=None):
        '''
            dvs[0]: 显卡设备，应该传入torch.device('cuda')
            dvs[1]: CPU设备，应该传入torch.device('cpu')
            dvs如果都传入torch.device('cpu')，则是完全CPU存储和计算
                如果都传入torch.device('cuda')，则是完全显卡存储和计算
            dvs[0]=dvs[1]的时候，可以不传列表，直接传一个dv就可以了
            nets: 小模型列表
            opts: 每个小模型对应的可选参数列表，如果要做训练，需要传入该项，opts需要和nets一一对应
            win_size: 显卡里最多存放多少个nets里的小模型，多线程的时候用处会比较大（后续开发），单线程的时候也是越大越好
            backward_deal: 梯度反向传播后的调用函数，训练的时候要传，本框架代码在第i个小模型梯度反向传播后会调用backward_deal(nets[i], opts[i])，里面加上梯度反向传播后需要做的代码，如果只是测试(eval)，不训练，该项可以不传
            dvs_nets: 不做缓存的小模型列表。如果要一部分做缓存，一部分不做，并且不做的那部分也放到nets和opts里了（方便统一调用backward_deal），则需要在这里单独再放一下，如果不做的部分没放在nets和opts里，则不需要传该参数
                dvs_nets = None or len(dvs_nets) == 1 or len(dvs_nets)==2
                dvs_nets[0]=None or [model1,model2,...] 固定在dvs[0]设备
                dvs_nets[1]=None or [model1,model2,...] 固定在dvs[1]设备，如果len(dvs_nets)==1则没有这项
        '''
        if fc_inputs_to is None:
            fc_inputs_to = self.inputs_to
        self.fc_inputs_to = fc_inputs_to
        if type(dvs) not in (list,tuple):
            dvs = [dvs]
        self.gdv = dvs[0]
        self.cdv = dvs[-1]
        self.dvs = dvs
        if dvs_nets is None:
            dvs_nets = [[]]
        if type(dvs_nets) not in (list, tuple):
            dvs_nets = [dvs_nets]
        dvs_nets = [k if k is not None else [] for k in dvs_nets]
        ids_nocache = set()
        fcs = []
        for i in range(len(dvs_nets)):
            for net in dvs_nets[i]:
                fc = net.register_forward_pre_hook(self.hook_forward_pre_tensor(i))
                fcs.append(fc)
                ids_nocache.add(id(net))
        self.ids_nocache = ids_nocache
        self.dvs_nets = dvs_nets
        fcs += [net.register_forward_pre_hook(self.hook_forward_pre) for net in nets if id(net) not in ids_nocache]
        fcs+=[net.register_forward_hook(self.hook_forward) for net in nets if id(net) not in ids_nocache]
        net = nets[0]
        if hasattr(net, "register_full_backward_hook"):
            fcs+=[net.register_full_backward_hook(self.hook_backward) for net in nets]
        else:
            fcs+=[net.register_backward_hook(self.hook_backward) for net in nets]
        self.src_nets = nets
        self.fcs = fcs
        self.nets = {id(net):net for net in nets}
        self.ctxs = {id(net):[] for net in nets}
        if opts is not None:
            opts = {id(net): opt for net,opt in zip(nets, opts)}
        self.opts = opts
        self.pools = []
        self.win_size = win_size
        self.backward_deal = backward_deal
        self.nears = {id(net):[-1,-1] for net in nets}
        self.curr = -1
        self.done_backward = -1
        self.no_caches = True
    def remove(self):
        [fc.remove() for fc in self.fcs]
    def hook_forward_pre_tensor(self, i):
        def hook(model, ins):
            model.to(self.dvs[i])
            ins = self.fc_inputs_to(ins, self.dvs[i])
            return ins
        return hook
    @staticmethod
    def inputs_to(inputs, dv):
        if isinstance(inputs, torch.Tensor):
            return inputs.to(dv)
        inputs = tuple([k.to(dv) for k in inputs])
        return inputs
    def ctxs_to(self, i, dv):
        if dv is None:
            self.ctxs[i] = []
        else:
            self.ctxs[i] = [k.to(dv) for k in self.ctxs[i]]
    def copy_backward(self, nid):
        for c_id in self.pools:
            self.nets[c_id].to(self.cdv)
            self.ctxs_to(c_id, None)
        self.pools = []
        self.nets[nid].to(self.gdv)
        self.ctxs_to(nid, self.gdv)
        self.pools.append(nid)
        next_id = nid
        for i in range(self.win_size-1):
            next_id = self.nears[next_id][1]
            if next_id<0:
                break
            self.nets[next_id].to(self.gdv)
            self.ctxs_to(next_id, self.gdv)
            self.pools.append(next_id)
    def copy_forward(self, nid, model):
        for c_id in self.pools:
            self.nets[c_id].to(self.cdv)
            self.ctxs_to(c_id, self.cdv)
        self.pools = []
        model.to(self.gdv)
        self.pools.append(nid)
        next_id = nid
        for i in range(self.win_size-1):
            next_id = self.nears[next_id][0]
            if next_id<0:
                break
            self.nets[next_id].to(self.gdv)
            self.pools.append(next_id)
    def hook_forward(self, model, ins, outs):
        self.no_caches = True
    def hook_forward_pre(self, model, ins):
        self.no_caches = False
        nid = id(model)
        #print(f"hook_forward_pre {nid}")
        if nid not in self.pools:
            self.copy_forward(nid, model)
        if self.curr>=0:
            self.nears[self.curr][0] = nid
        self.curr = nid
        return self.fc_inputs_to(ins, self.gdv)
    def do_forward(self, fc):
        #print("FWD")
        self.no_caches = True
        self.ctxs = {k:[] for k in self.nets}
        with torch.autograd.graph.saved_tensors_hooks(self.hook_pack, self.hook_unpack):
            rst = fc()
        #print("DFWD")
        return rst.to(self.gdv)
    def wrap_backward_deal(self, net_id):
        if self.backward_deal is None:
            return
        self.backward_deal(self.nets[net_id], self.opts[net_id])
    def hook_backward(self, model, grad_ins, grad_outs):
        nid = id(model)
        #print(f"hook_backward {nid}")
        self.wrap_backward_deal(nid)
    def hook_pack(self, dt):
        #print(f"pack")
        if self.no_caches:
            # 不做缓存，数据不处理
            return -1, dt
        index = self.curr
        # forward时候为了后面计算梯度存的缓存，放到列表里方便转cpu和gpu
        self.ctxs[index].append(dt)
        return index, len(self.ctxs[index])-1
    def hook_unpack(self, x):
        nid = x[0]
        #print(f"unpack {nid}")
        if nid<0:
            return x[1]
        if nid not in self.pools:
            self.copy_backward(nid)
        dt = self.ctxs[nid][x[1]]
        if self.curr>=0:
            self.nears[self.curr][1] = nid
        self.curr = nid
        return dt
    def do_backward(self, fc):
        self.curr = -1
        fc()
