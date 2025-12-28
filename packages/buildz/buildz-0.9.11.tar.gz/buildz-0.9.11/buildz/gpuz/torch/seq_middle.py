#
import torch
from torch import nn
import threading as th
'''
注：
代码有误，原本以为register_full_backward_hook的勾子函数是在模型反向梯度计算之前调用的，后来发现是反向梯度计算之后调用的，本来本代码使用局限就比较多（要求拆分的模型线性连接），直接重写了个buildz.gpuz.torch.dict_middle作为代替，本代码暂时先放着，后续会做修改或者删除
'''
class SeqCache:
    '''
        用处：显存不够，同时模型可以拆成多个小模型线性连接的时候，可以用本代码，本代码会在forward和backward的时候自动把小的多层网络轮流放到gpu里计算，计算完再转cpu里
        需要使用者手动将多层网络拆分成多个更小一点的多层网络
        测试代码见test_moddle_conv1.py
        大概有纯显卡二分之一到三分之一的性能，起码比cpu好，尤其是进行卷积计算，比cpu好太多
        代码例子:
        
        from buildz.gpuz.torch import CacheModel
        from torch import nn,optim
        model1 = nn.Sequential(*[nn.Linear(1024,1024) for i in range(10)])
        model2 = nn.Sequential(*[nn.Linear(1024,1024) for i in range(10)])
        model3 = nn.Sequential(*[nn.Linear(1024,1024) for i in range(10)])
        opt1 = optim.Adam(model1.parameters(), lr=0.001)
        opt2 = optim.Adam(model2.parameters(), lr=0.001)
        opt3 = optim.Adam(model3.parameters(), lr=0.001)
        models = [model1,model2,model3]
        opts = [opt1,opt2,opt3]
        loss_fn = torch.nn.MSELoss()
        def opt_step(net, opt):
            # 如果模型只是用来测试，不做训练，可以不传该函数，同时opts传入空就可以
            # 对模型的一些其他优化，可以写可以不写，主要是调用opt.step()进行当前小模型的模型训练
            # torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
            opt.step()
        cmodel = CacheModel(torch.device('cuda'), torch.device('cpu'),models,opts,3,opt_step)

        # 训练:
        [md.train() for md in models]
        for inputs,targets in dataloader: #批量数据集，这个自己实现
            [opt.zero_grad() for opt in opts]
            outs = cmodel.do_forward(inputs)
            loss = loss_fn(outs, targets)
            cmodel.do_backward(lambda: loss.backward())
            # opt.step()在do_backward里会自动调用
            print(loss.item())

        # 测试:
        with torch.no_grad():
            outputs = cmodel.do_forward(inputs)
        print(outputs)
    '''
    def __init__(self, gdv, cdv, nets, opts, win_size = 1, backward_deal = None):
        '''
            gdv: 显卡设备，应该传入torch.device('cuda')
            cdv: CPU设备，应该传入torch.device('cpu')
            gdv和cdv如果都传入torch.device('cpu')，则是完全CPU存储和计算
                如果都传入torch.device('cuda')，则是完全显卡存储和计算
        '''
        self.gdv = gdv
        self.cdv = cdv
        # event和condition未使用，本来打算做成多线程，但python线程一次只能有一个在运行，抢占有点严重，待修改
        self.event = th.Event()
        self.condition=th.Condition()
        [net.register_full_backward_hook(self.hook_backward) for net in nets]
        self.nets = nets
        self.size = len(nets)
        self.ctxs = [[] for i in range(self.size)]
        self.size_1 = self.size-1
        self.opts = opts
        self.win_size = win_size
        self.backward_deal = backward_deal
        self.base = -1
        self.curr = 0
        self.last = -1
        self.running = False
    def hook_pack(self, dt):
        # forward时候为了后面计算梯度存的缓存，放到列表里方便转cpu和gpu
        self.ctxs[self.curr].append(dt)
        return len(self.ctxs[self.curr])-1
    def hook_unpack(self, x):
        dt = self.ctxs[self.curr][x]
        return dt
    def nfc(self, fc, *a,**b):
        [getattr(net, fc)(*a,**b) for net in self.nets]
    def reset(self):
        for i in range(self.base,self.last+1):
            self.nets[i].to(self.cdv)
            self.ctxs_to(i, self.cdv)
        self.base,self.last=-1,-1
    def ctxs_to(self, i, dv):
        if dv is None:
            self.ctxs[i] = []
        else:
            self.ctxs[i] = [k.to(dv) for k in self.ctxs[i]]
    def copy_backward(self):
        if self.last<self.curr:
            self.reset()
        if self.base==0:
            return False
        if self.last<0:
            self.nets[self.size_1].to(self.gdv)
            self.last = self.size_1
            self.base = self.size_1
        diff = self.win_size-(self.last-self.base+1)
        diff = min(diff, self.base)
        for i in range(diff):
            self.nets[self.base-1].to(self.gdv)
            self.ctxs_to(self.base-1, self.gdv)
            self.base-=1
        rels = self.last-self.curr
        for i in range(rels):
            self.nets[self.last].to(self.cdv)
            self.ctxs_to(self.last, None)
            self.last-=1
        return True
    def copy_forward(self):
        if self.base>self.curr:
            self.reset()
        if self.last==self.size_1:
            return False
        if self.base<0:
            self.nets[0].to(self.gdv)
            self.base=0
            self.last=0
        diff = self.win_size-(self.last-self.base+1)
        diff = min(diff, self.size_1-self.last)
        for i in range(diff):
            self.nets[self.last+1].to(self.gdv)
            self.last+=1
        rels = self.curr-self.base
        for i in range(rels):
            self.nets[self.base].to(self.cdv)
            self.ctxs_to(self.base, self.cdv)
            self.base+=1
        return True
    def th_copy_forward(self):
        while self.copy_forward():
            self.event.set()
        self.running = False
    def th_copy_backward(self):
        while self.copy_backward():
            self.event.set()
    def wait(self):
        with self.condition:
            self.condition.notify()
        self.event.wait()
    def do_forward(self, inputs):
        # while self.running:
        #     import time
        #     time.sleep(0.01)
        # t = th.Thread(target=self.th_copy_forward, daemon=True)
        # self.running = True
        # t.start()
        self.ctxs = [[] for i in range(self.size)]
        with torch.autograd.graph.saved_tensors_hooks(self.hook_pack, self.hook_unpack):
            rst = self.forward(inputs)
        return rst
    def forward(self, inputs):
        for self.curr in range(len(self.nets)):
            while not (self.base<=self.curr<=self.last):
                self.copy_forward()
                #self.wait()
            inputs = self.nets[self.curr](inputs)
        return inputs
    def wrap_backward_deal(self, i):
        if self.backward_deal is None:
            return
        try:
            self.backward_deal(self.nets[i], self.opts[i])
        finally:
            pass
    def hook_backward(self, model, ins, outs):
        if self.backward_curr<self.size_1:
            self.wrap_backward_deal(self.backward_curr+1)
        self.curr = self.backward_curr
        while not (self.base<=self.backward_curr<=self.last):
            #self.wait()
            self.copy_backward()
        self.backward_curr-=1
    def do_backward(self, fc):
        self.backward_curr=self.curr
        # t = th.Thread(target=self.th_copy_backward,daemon=True)
        # t.start()
        fc()
        self.wrap_backward_deal(0)

pass
