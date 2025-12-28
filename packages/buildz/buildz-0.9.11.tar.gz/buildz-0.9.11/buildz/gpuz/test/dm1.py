
from buildz.gpuz.torch.middle_cache import MiddleCache
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
dims = 64
"""
cd D:\rootz\python\gits\buildz_upd\buildz\gpuz\test
D:
python -m buildz.gpuz.test.demo > demo.txt

"""
dataset = TestDataset(90, dims)
dataloader = DataLoader(dataset, 30)
class MiniModel(nn.Module):
    def __init__(self, dims, mdims, num):
        super().__init__()
        nets = [nn.Linear(dims, mdims)]
        nets += [nn.Linear(mdims,mdims) for i in range(num)]
        nets.append(nn.Linear(mdims,dims))
        self.nets = nn.Sequential(*nets)
    def forward(self, inputs):
        return self.nets(inputs)
models = [MiniModel(dims, 32, 3) for i in range(6)]
#opts = [optim.Adam(model.parameters(), lr=0.001) for model in models]
real_model = nn.Sequential(*models)
opt = optim.Adam(real_model.parameters(), lr=0.001)
#可以指定哪些模型全部放cuda或者全部放cpu
cuda_models = [models[1],models[2]]
cpu_models = [models[-1]]
loss_fn = torch.nn.MSELoss()
cache = MiddleCache(models, 3)#, cal_dv = "cpu", cal_nets = cuda_models, cache_nets = cpu_models)#, [torch.device('cuda'), torch.device('cpu')],models,opts,3,opt_step)#, [cuda_models,cpu_models])

# 训练:
def train():
    cache.train()
    _loss = 0
    for inputs,targets in dataloader:
        targets = targets.cuda()
        #inputs,targets = inputs.cuda(),targets.cuda()
        opt.zero_grad()
        with cache.wrap_forward():
            outs = real_model(inputs)
        loss = loss_fn(outs, targets)
        with cache.wrap_backward():
            loss.backward()
        torch.nn.utils.clip_grad_norm_(real_model.parameters(), max_norm=1.0)
        opt.step()
        _loss+=loss.cpu().item()
        #cache.do_backward(lambda: loss.backward())
        # opt.step()在do_backward里会自动调用
        # print(loss.item())
        # break
        #break
    return _loss / (len(dataloader))
pass
import time
print("start")
start = time.time()
for i in range(50):
    print(train())
sec = time.time()-start
print("time cost:", sec)

"""
python -m buildz.gpuz.test.dm1

from buildz.gpuz.test import dm1 as dm

dm.cache.train()
inputs, targets = list(dm.dataloader)[0]
dm.opt.zero_grad()
with dm.cache.wrap_forward():
    outs = dm.real_model(inputs)

pass

ks = list(dm.cache.datas.keys())
dts0 = dm.cache.datas[ks[0]]
net0 = dm.cache.nets[ks[0]]
[k.shape for k in dts0]


dts1 = dm.cache.datas[ks[1]]
net1 = dm.cache.nets[ks[1]]
[k.shape for k in dts1]


ws = []
for md in dm.models:
    for net in md.nets:
        ws.append(net.weight.cpu().detach().clone())

pass

dm.train()

nws = []
for md in dm.models:
    for net in md.nets:
        nws.append(net.weight.cpu().detach().clone())

pass
subs = [(a-b).sum() for a,b in zip(ws, nws)]

w0 = dm.models[0].nets[-1].weight.cpu().detach()
w1 = dm.models[1].nets[0].weight.cpu().detach()

dm.train()

nw0 = dm.models[0].nets[-1].weight.cpu().detach()
nw1 = dm.models[1].nets[0].weight.cpu().detach()

(w0-nw0).sum()
(w1-nw1).sum()

"""