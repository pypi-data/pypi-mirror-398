
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
cache = DictCache([torch.device('cuda'), torch.device('cpu')],models,opts,3,opt_step)#, [cuda_models,cpu_models])

# 训练:
def train():
    [md.train() for md in models]
    for inputs,targets in dataloader:
        inputs,targets = inputs.cuda(),targets.cuda()
        [opt.zero_grad() for opt in opts]
        outs = cache.do_forward(lambda:real_model(inputs))
        loss = loss_fn(outs, targets)
        cache.do_backward(lambda: loss.backward())
        # opt.step()在do_backward里会自动调用
        #print(loss.item())
        #break
pass
import time
print("start")
start = time.time()
for i in range(50):
    train()
sec = time.time()-start
print("time cost:", sec)
"""
from buildz.gpuz.test import dm

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

"""