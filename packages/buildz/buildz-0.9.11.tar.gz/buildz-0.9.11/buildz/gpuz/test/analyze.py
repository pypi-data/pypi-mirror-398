#

import sys
from buildz.gpuz.torch import DictCache
import torch,time
from torch import nn,optim
cpu = torch.device('cpu')
cuda = cpu
if torch.cuda.is_available():
    cuda = torch.device('cuda')
def sz(tensor):
    return tensor.element_size()*tensor.nelement()
def unit_sz(net):
    rst = 0
    for key in "weight,bias".split(","):
        if hasattr(net, key):
            rst+=sz(getattr(net,key))
    return rst

pass
dvs = [cpu,cuda]
def show_size(sz):
    u = None
    for unit in "B,KB,MB,GB".split(","):
        u=unit
        if sz<256:
            break
        sz = sz/1024
    return sz, unit

def default_fc_opt(net, opt):
    torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
    opt.step()
def analyze(use_cache, use_cuda, mark_train, loop, fc_gen, dataloader, loss_fn, fc_opt, win_size):
    tmp = list(fc_gen())
    mds = tmp.pop(0)
    gmodel = tmp.pop(0)
    opts = tmp.pop(0)
    gopt = tmp.pop(0)
    dvs_nets = None
    if len(tmp)>0:
        dvs_nets = tmp.pop(0)
    dv = cuda
    if not use_cuda:
        use_cache = False
    cache = None
    if use_cache:
        cache = DictCache([cuda, cpu], mds, opts, win_size, fc_opt, dvs_nets)
    if not use_cuda:
        dv = cpu
    if not use_cache:
        gmodel = gmodel.to(dv)
    s_val = "mean loss"
    if mark_train:
        if not use_cache:
            gmodel.train()
        else:
            [md.train() for md in mds]
    else:
        s_val = "mean value"
        if not use_cache:
            gmodel.eval()
        else:
            [md.eval() for md in mds]
    times = []
    for i in range(loop):
        total_loss = 0
        curr=time.time()
        if mark_train:
            for dt,tgt in dataloader:
                dt=dt.to(dv)
                tgt = tgt.to(dv)
                if not use_cache:
                    gopt.zero_grad()
                    out = gmodel(dt)
                    loss = loss_fn(out, tgt)
                    loss.backward()
                    fc_opt(gmodel, gopt)
                else:
                    [opt.zero_grad() for opt in opts] #写gopt.zero_grad()应该也可以，只是删掉之前计算的梯度
                    out = cache.do_forward(lambda :gmodel(dt)) # 其实只是加了勾子函数，实际的计算还是模型计算
                    loss = loss_fn(out, tgt)
                    cache.do_backward(lambda : loss.backward()) # 加勾子函数
                total_loss+=loss.item()
        else:
            with torch.no_grad():
                for dt,tgt in dataloader:
                    dt=dt.to(dv)
                    if not use_cache:
                        out = gmodel(dt)
                    else:
                        out = cache.do_forward(lambda :gmodel(dt)) # 其实只是加了勾子函数，实际的计算还是模型
                    total_loss+=out.mean().item()
        sec = time.time()-curr
        print(" train:", i, s_val+":", total_loss/len(dataloader), "time:", sec)
        times.append(sec)
    # 清理显存
    del gmodel, gopt, mds, opts
    torch.cuda.empty_cache()
    return times
        
def analyzes(mark_train, loop, fc_gen, dataloader, loss_fn = None, fc_opt = None, win_size=3, modes = ['cuda', 'cache','cpu']):
    '''
        mds, gmodel, opts, gopt = fc_gen()
    '''
    if type(modes)==str:
        modes = modes.split(",")
    if loss_fn is None:
        loss_fn = torch.nn.MSELoss()
    if fc_opt is None:
        fc_opt = default_fc_opt
    if 'gpu' in modes:
        modes = list(modes)+['cuda']
    print(f"modes: {modes}")
    # 正常做法：只用显卡
    if 'cuda' in modes:
        print("No Used DictCache")
        gtimes = analyze(False, True, mark_train, loop, fc_gen, dataloader, loss_fn, fc_opt, win_size)
        gtimes = gtimes[1:] # 第一次计算因为加载cuda一些东西会比较慢，不计算在内
        torch.cuda.empty_cache()
    # 显卡不足的时候：模型只在计算的时候存入显卡显存
    if 'cache' in modes:
        print("Using DictCache:")
        dc_times = analyze(True, True, mark_train, loop, fc_gen, dataloader, loss_fn, fc_opt, win_size)
        dc_times = dc_times[1:]
        torch.cuda.empty_cache()
    # 不用显卡，只用CPU
    if 'cpu' in modes:
        print("Using CPU:")
        cpu_times = analyze(False, False, mark_train, loop, fc_gen, dataloader, loss_fn, fc_opt, win_size)
        cpu_times = cpu_times[1:]
        torch.cuda.empty_cache()
    print(f"\nAnalyze")
    if 'cuda' in modes:
        print(f"    mean time cost not used DictCache: {sum(gtimes)/len(gtimes)} sec")
    if 'cache' in modes:
        print(f"    mean time cost using DictCache: {sum(dc_times)/len(dc_times)} sec")
    if 'cpu' in modes:
        print(f"    mean time cost using CPU: {sum(cpu_times)/len(cpu_times)} sec")