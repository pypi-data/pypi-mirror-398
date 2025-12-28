#

import sys
from buildz.gpuz.torch import DictCache
from buildz.gpuz.test import analyze
from buildz import pyz
import math
import torch,time
from torch import nn,optim
from torch.utils.data import DataLoader, Dataset
cpu,cuda = analyze.dvs
MultiheadAttention = nn.MultiheadAttention
class PostionalEncoding(nn.Module):
    def __init__(self, word_size, max_length, batch_first=False):
        super().__init__()
        pos = torch.arange(max_length).unsqueeze(1)
        words = torch.arange(word_size)
        mod2 = words%2
        offset = torch.pi*0.5*mod2
        # exp(log(A)*B)等价于A^B
        x = pos*torch.exp(-math.log(1e4)*(words-mod2)/word_size)
        data = torch.sin(x+offset)
        data.requires_grad=False
        if batch_first:
            data = data.unsqueeze(0)
        else:
            data = data.unsqueeze(1)
        self.vecs = nn.Parameter(data, requires_grad=False)
        self.batch_first = batch_first
    def forward(self, ins):
        if self.batch_first:
            ins = ins + self.vecs[:, :ins.size(1)]
        else:
            ins = ins + self.vecs[:ins.size(1)]
        return ins
def make_linear(input_size, middle_size, middle_fc):
    if middle_size is not None:
        nets = []
        nets.append(nn.Linear(input_size, middle_size))
        if middle_fc is not None:
            nets.append(middle_fc())
        nets.append(nn.Linear(middle_size, input_size))
        linear = nn.Sequential(*nets)
    else:
        linear = nn.Linear(input_size, input_size)
    return linear
class Decoder(nn.Module):
    def __init__(self, word_dims, num_heads=1, kv_dims=None, batch_first=False, bias=True, linear_size=None, linear_fc = nn.ReLU):
        super().__init__()
        self.self_multi = MultiheadAttention(word_dims,num_heads,bias=bias,batch_first=batch_first,kdim=kv_dims,vdim=kv_dims)
        self.linear = make_linear(word_dims, linear_size, linear_fc)
        self.ln1 = nn.LayerNorm(word_dims)
        self.ln2 = nn.LayerNorm(word_dims)
        self.batch_first = batch_first
    def forward(self, outputs, outs_mask):
        self_attn, _ = self.self_multi(outputs,outputs,outputs, attn_mask=outs_mask)
        outputs = self.ln1(outputs+self_attn)
        outputs = self.ln2(outputs+self.linear(outputs)) 
        return outputs
class DecodePart(nn.Module):
    def __init__(self, num_words, word_dims, sequence_length, num_decoders=6, num_heads=1, kv_dims=None, batch_first=False, bias=True, linear_size=None, linear_fc = nn.ReLU):
        super().__init__()
        self.embedding = nn.Embedding(num_words, word_dims)
        self.pos_encoding = PostionalEncoding(word_dims, sequence_length, batch_first)
        self.num_decoders = num_decoders
        decoders = [Decoder(word_dims, num_heads, kv_dims, batch_first, bias, linear_size, linear_fc) for i in range(num_decoders)]
        self.src_decoders = decoders
        self.decoders = nn.ModuleList(decoders)
    def mds(self):
        return [self.embedding, self.pos_encoding]+self.src_decoders 
    def forward(self, outputs, outs_mask):
        outputs = self.embedding(outputs)
        outputs = self.pos_encoding(outputs)
        for decoder in self.decoders:
            outputs = decoder(outputs, outs_mask)
        return outputs
class Chats(nn.Module):
    def __init__(self, num_words_outputs, word_dims, sequence_length_outputs, num_decoders=6, num_heads=1, kv_dims=None, batch_first=False, bias=True, linear_size=None, linear_fc = nn.ReLU, mask_index = -1):
        super().__init__()
        self.decode = DecodePart(num_words_outputs, word_dims, sequence_length_outputs, num_decoders, num_heads, word_dims, batch_first, bias, linear_size, linear_fc)
        self.linear = nn.Linear(word_dims, num_words_outputs)
        self.sequence_length_outputs = sequence_length_outputs
        self.mask_index = mask_index
        self.batch_first = batch_first
        self.num_heads = num_heads
    def mds(self):
        return [self.linear]+self.decode.mds()
    def gen_masks(self, outputs):
        if self.batch_first:
            batch_id, dt_id=0,1
        else:
            batch_id, dt_id=1,0
        batch_size, outs_len = outputs.size(batch_id), outputs.size(dt_id)
        mask = torch.ones(batch_size, self.num_heads, outs_len, outs_len)
        mask = torch.triu(mask, diagonal=1)
        outs_mask = mask.to(torch.bool)
        if self.mask_index>=0:
            outs_mask_1 = (outputs==self.mask_index).unsqueeze(1).unsqueeze(1)
            if not self.batch_first:
                outs_mask_1 = outs_mask_1.transpose(0,3)
            if self.num_heads>1 or outs_len>1:
                outs_mask_1 = outs_mask_1.expand(batch_size, self.num_heads, outs_len, outs_len)
            outs_mask = outs_mask | outs_mask_1
        outs_mask = outs_mask.reshape(-1, outs_len, outs_len).bool().to(outputs.device)
        return outs_mask
    def forward(self, outputs):
        outs_mask = self.gen_masks(outputs)
        rst = self.decode(outputs, outs_mask)
        rst = self.linear(rst)
        return rst

class TestDataset(Dataset):
    def __init__(self, num, std_len, words):
        self.num = num
        self.datas = torch.randint(0, words, (num,std_len))
        sz = analyze.sz(self.datas)
        sz, unit = analyze.show_size(sz)
        print(f"data size: {sz} {unit}")
    def __len__(self):
        return self.num
    def __getitem__(self, i):
        return self.datas[i], self.datas[i]

pass

def test():
    num_words_outputs = 1024
    word_dims = 512
    sequence_length_outputs = 512
    num_decoders=12
    num_heads=8
    loop = 5
    num_datas = 60
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
    if len(args)>0:
        num_decoders = int(args.pop(0))
    print(f"num_decoders: {num_decoders}")
    ds = TestDataset(num_datas, sequence_length_outputs, num_words_outputs)
    dl = DataLoader(ds, batch)
    def fc_gen():
        gmodel = Chats(num_words_outputs, word_dims, sequence_length_outputs, num_decoders, num_heads, batch_first=1)
        mds = gmodel.mds()
        opts =[optim.Adam(md.parameters(), lr=lr) for md in mds]
        gopt = optim.Adam(gmodel.parameters(), lr=lr)
        return mds, gmodel, opts, gopt
    def fc_opt(net, opt):
        torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
        opt.step()
    loss_fn = nn.CrossEntropyLoss()
    def wrap_fn(outs, targets):
        outs = outs.view(-1, outs.shape[-1])
        targets = targets.reshape(-1)
        return loss_fn(outs, targets)
    analyze.analyzes(mark_train, loop, fc_gen, dl, wrap_fn, fc_opt, win_size, modes)

pyz.lc(locals(),test)