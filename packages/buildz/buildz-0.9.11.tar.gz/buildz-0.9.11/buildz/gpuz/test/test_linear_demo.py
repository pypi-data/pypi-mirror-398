#

import sys
from buildz.gpuz.torch import DictCache
from buildz.gpuz.test import analyze
from buildz import pyz
import torch,time
from torch import nn,optim
from torch.utils.data import DataLoader, Dataset
cpu,cuda = analyze.dvs
class Model(nn.Module):
    def __init__(self, dims, num):
        super().__init__()
        nets=[]
        for i in range(num):
            nets.append(nn.Linear(dims,dims))
            nets.append(nn.LeakyReLU())
        self.nets = nn.Sequential(*nets)
    def forward(self, inputs):
        return self.nets(inputs)
    def size(self):
        return sum([analyze.unit_sz(net) for net in self.nets])

pass
class TestDataset(Dataset):
    def __init__(self, n, dims):
        self.n = n
        self.dims = dims
        self.datas = torch.rand(n, dims)
        sz = analyze.sz(self.datas)
        sz, unit = analyze.show_size(sz)
        print(f"data size: {sz} {unit}")
    def __len__(self):
        return self.n
    def __getitem__(self, i):
        return self.datas[i], self.datas[i]

pass

def test():
    '''
        这些参数是不用DictCache的时候8GB显存刚好能跑
        测试显存不够用的情况，要么用其他程序占显存，要么改参数，num改大一些显存就不够用了
        也提供了个占用显存的简单代码:
            占用3GB显存：
                python -m buildz.gpuz.test.take_gpu_mem 12
            占用4GB显存：
                python -m buildz.gpuz.test.take_gpu_mem 20

    '''
    nets=10
    dims=2000
    loop = 5
    datas = 60
    batch=30
    lr=0.0001
    win_size=3
    args = sys.argv[1:]
    mark_train = True
    if len(args)>0:
        mark_train = args.pop(0).lower()=='train'
    modes = 'cuda,cache,cpu'
    if len(args)>0:
        modes = args.pop(0)
    num = 12
    if len(args)>0:
        num = int(args.pop(0))
    print(f"num: {num}")
    def fc_gen():
        mds = [Model(dims, nets) for i in range(num)]
        mds_sz = [md.size() for md in mds]
        sz, unit = analyze.show_size(sum(mds_sz))
        print(f"Model Size: {sz} {unit}")
        opts =[optim.Adam(md.parameters(), lr=lr) for md in mds]
        gmodel = nn.Sequential(*mds)
        gopt = optim.Adam(gmodel.parameters(), lr=lr)
        return mds, gmodel, opts, gopt
    def fc_opt(net, opt):
        torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
        opt.step()
    ds = TestDataset(datas, dims)
    dl = DataLoader(ds, batch)
    loss_fn = torch.nn.MSELoss()
    analyze.analyzes(mark_train, loop, fc_gen, dl, loss_fn, fc_opt, win_size, modes)

pyz.lc(locals(),test)