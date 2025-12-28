#

import sys
from buildz.gpuz.torch import DictCache
from buildz.gpuz.test import analyze
from buildz import pyz
import torch,time
from torch import nn,optim
from torch.utils.data import DataLoader, Dataset
cpu,cuda = analyze.dvs
class ConvModel(nn.Module):
    def __init__(self, dims, num, ins_channels, middle_channels):
        super().__init__()
        nets=[]
        for i in range(num):
            nets.append(nn.Conv2d(ins_channels, middle_channels, 5, padding=2))
            nets.append(nn.Conv2d(middle_channels, ins_channels, 5, padding=2))
            nets.append(nn.LeakyReLU())
        self.nets = nn.Sequential(*nets)
    def forward(self, inputs):
        return self.nets(inputs)
    def size(self):
        return sum([analyze.unit_sz(net) for net in self.nets])

pass
class ResNet(nn.Module):
    def __init__(self, net):
        super().__init__()
        self.net = net
    def forward(self, inputs):
        return inputs+self.net(inputs)
class TestDataset(Dataset):
    def __init__(self, n, dims, channels):
        self.n = n
        self.dims = dims
        self.datas = torch.rand(n, channels, dims,dims)
        sz = analyze.sz(self.datas)
        sz, unit = analyze.show_size(sz)
        print(f"data size: {sz} {unit}")
    def __len__(self):
        return self.n
    def __getitem__(self, i):
        return self.datas[i], self.datas[i]

pass
def gen(dims, nets_num, channels, middle_channels, num_conv, lr):
    """
        类似UNet的模型
    """
    mds = []
    base = None
    for i in range(num_conv):
        nets = [ConvModel(dims, nets_num, channels, middle_channels) for i in range(2)]
        mds+=nets
        if base is not None:
            nets = [nets[0], base, nets[1]]
        nets = nn.Sequential(*nets)
        base = ResNet(nets)
    fullnet = base
    opts =[optim.Adam(md.parameters(), lr=lr) for md in mds]
    gopt = optim.Adam(fullnet.parameters(), lr=lr)
    mds_sz = [md.size() for md in mds]
    sz, unit = analyze.show_size(sum(mds_sz))
    print(f"Model Size: {sz} {unit}")
    return mds, fullnet, opts, gopt
    


def fc_opt(net, opt):
    torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
    opt.step()
def test():
    nets=2
    channels=10
    middle_channels = 30
    dims=512
    loop = 10
    datas = 6
    batch=2
    '''
        如果batch改成6，不用DictCache的时候8GB显存的显卡直接报错显存不够；用DictCache并且win_size=3时需要5GB显存，训练一次9秒；用cpu则要跑很久很久很久
    '''
    # batch=6
    lr=0.0001
    win_size=3
    num_conv = 12
    args = sys.argv[1:]
    mark_train = True
    if len(args)>0:
        mark_train = args.pop(0).lower()=='train'
    modes = 'cuda,cache,cpu'
    if len(args)>0:
        modes = args.pop(0)
    if len(args)>0:
        num_conv = int(args.pop(0))
    print(f"num_conv: {num_conv}")
    ds = TestDataset(datas, dims, channels)
    dl = DataLoader(ds, batch)
    loss_fn = torch.nn.MSELoss()
    def fc_gen():
        return gen(dims, nets, channels, middle_channels, num_conv, lr)
    analyze.analyzes(mark_train, loop, fc_gen, dl, loss_fn, fc_opt, win_size, modes)

pyz.lc(locals(),test)