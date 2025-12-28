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
    def __init__(self, dims, ins_channels, middle_channels):
        super().__init__()
        nets=[]
        nets.append(nn.Conv2d(ins_channels, middle_channels, 5, padding=2))
        nets.append(nn.LeakyReLU())
        self.nets = nn.Sequential(*nets)
    def forward(self, inputs):
        return self.nets(inputs)
    def size(self):
        return sum([analyze.unit_sz(net) for net in self.nets])

pass
class UNet(nn.Module):
    def __init__(self, encoder, dealer, decoder):
        super().__init__()
        self.encoder, self.dealer, self.decoder = encoder, dealer, decoder
    def forward(self, inputs):
        tmp = self.encoder(inputs)
        out = tmp
        if self.dealer is not None:
            out = self.dealer(tmp)
        tmp = torch.cat([tmp, out], dim=1)
        return self.decoder(tmp)
class ResNet(nn.Module):
    def __init__(self, net):
        super().__init__()
        self.net = net
    def forward(self, inputs):
        return inputs+self.net(inputs)
class TestDataset(Dataset):
    def __init__(self, num, dims, channels, outs_dims):
        self.num = num
        self.dims = dims
        self.datas = torch.rand(num, channels, dims,dims)
        self.targets = torch.rand(num, outs_dims)
        sz = analyze.sz(self.datas)+analyze.sz(self.targets)
        sz, unit = analyze.show_size(sz)
        print(f"data size: {sz} {unit}")
    def __len__(self):
        return self.num
    def __getitem__(self, i):
        return self.datas[i], self.targets[i]

pass
class LnsNet(nn.Module):
    def __init__(self, input_dims, outs_dims, num):
        super().__init__()
        curr_dims = input_dims
        lns = []
        for i in range(num):
            rate = (i+1)/num
            dims = int(input_dims*(1-rate)+outs_dims*rate)
            ln = nn.Linear(curr_dims, dims)
            lns.append(ln)
            lns.append(nn.LeakyReLU())
            curr_dims = dims
        self.nets = nn.Sequential(*lns)
    def forward(self, inputs):
        batch = inputs.size(0)
        inputs = inputs.reshape(batch, -1)
        return self.nets(inputs)
    def size(self):
        return sum([analyze.unit_sz(net) for net in self.nets])

def gen(dims, outs_dims, channels, num_conv, num_ln, lr):
    """
        类似UNet的模型，不过cat改成了resnet的加
    """
    mds = []
    curr = channels
    encoders = []
    decoders = []
    for i in range(num_conv):
        encoder = ConvModel(dims, curr, curr*2)
        decoder = ConvModel(dims, curr*4, curr)
        curr*=2
        encoders.append(encoder)
        decoders.append(decoder)
    base = None
    mds += encoders
    mds+=decoders
    print(f"curr:{curr}")
    for i in range(num_conv):
        e = encoders[num_conv-i-1]
        d = decoders[num_conv-i-1]
        base = UNet(e, base, d)
    cvnets = base
    input_dims = dims*dims*channels
    lns = LnsNet(input_dims, outs_dims, num_ln)
    print(lns)
    mds.append(lns)
    gmds = [lns]
    mds_sz = [md.size() for md in mds]
    fullnet = nn.Sequential(cvnets, lns)
    opts =[optim.Adam(md.parameters(), lr=lr) for md in mds]
    gopt = optim.Adam(fullnet.parameters(), lr=lr)
    sz, unit = analyze.show_size(sum(mds_sz))
    print(f"Model Size: {sz} {unit}, mds: {len(mds)}")
    return mds, fullnet, opts, gopt, [gmds, None]
    


def fc_opt(net, opt):
    torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
    opt.step()
def test():
    channels=3
    dims= 32
    out_dims = 10
    loop = 10
    datas = 6
    batch=2
    lr=0.0001
    win_size=3
    num_conv = 6
    num_ln = 2
    args = sys.argv[1:]
    mark_train = True
    if len(args)>0:
        mark_train = args.pop(0).lower()=='train'
    modes = 'cuda,cache,cpu'
    if len(args)>0:
        modes = args.pop(0)
    if len(args)>0:
        num_conv = int(args.pop(0))
    if len(args)>0:
        num_ln = int(args.pop(0))
    print(f"num_conv: {num_conv}, num_ln: {num_ln}")
    ds = TestDataset(datas, dims, channels, out_dims)
    dl = DataLoader(ds, batch)
    loss_fn = torch.nn.MSELoss()
    def fc_gen():
        return gen(dims, out_dims, channels, num_conv, num_ln, lr)
    analyze.analyzes(mark_train, loop, fc_gen, dl, loss_fn, fc_opt, win_size, modes)

pyz.lc(locals(),test)