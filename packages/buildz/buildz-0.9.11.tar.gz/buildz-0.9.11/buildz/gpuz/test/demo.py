
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
dims = 3
"""
cd D:\rootz\python\gits\buildz_upd\buildz\gpuz\test
D:
python -m buildz.gpuz.test.demo > demo.txt

"""
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
models = [MiniModel(dims, 6, 3) for i in range(6)]
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
[md.train() for md in models]
for inputs,targets in dataloader:
    inputs,targets = inputs.cuda(),targets.cuda()
    [opt.zero_grad() for opt in opts]
    outs = cache.do_forward(lambda:real_model(inputs))
    loss = loss_fn(outs, targets)
    cache.do_backward(lambda: loss.backward())
    # opt.step()在do_backward里会自动调用
    print(loss.item())
    break

exit()

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

pass

# 测试:
inputs = torch.rand(1, dims).cuda()
with torch.no_grad():
    outputs = real_model(inputs)
print(outputs)

