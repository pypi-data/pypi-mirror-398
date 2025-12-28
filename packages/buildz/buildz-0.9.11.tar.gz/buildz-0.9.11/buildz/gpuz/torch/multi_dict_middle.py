#
import torch
from torch import nn
import threading as th
from ... import Base
import numpy as np
'''
注：
没写好，还不能用
'''
class MultiDictCache(Base):
    def init(self, nets, win_sizes=None, backward_deal=None, fc_inputs_to=None, default_dv = None, default_win_size=1):
        '''
            nets: [
                net
                (net, run_dv)
                (net, run_dv, opt)
                (net, (run_dv, cache_dv), opt)
            ]
            win_sizes: {
                run_dv: size
            }
        '''
        if default_dv is None:
            default_dv = torch.device("cpu")
        if fc_inputs_to is None:
            fc_inputs_to = self.inputs_to
        self.fc_inputs_to = fc_inputs_to
        self.default_dv = default_dv
        if win_sizes is None:
            win_sizes = {}
        self.default_win_size = default_win_size
        self.win_sizes = win_sizes
        #run_dvs = {}
        rst = {}
        nears = {}
        for it in nets:
            if type(it) not in (list,tuple):
                it = [it]
            if len(it)==1:
                it.append(default_dv)
            x = it[1]
            if type(x) not in (list,tuple):
                it[1] = [it[1]]
            run_dvs.add(it[1][0])
            net = it[0]
            net_id = id(net0)
            rst[net_id] = it
            run_dv = it[1][0]
            if run_dv not in nears:
                nears[run_dv] = {}
            nears[run_dv][net_id] = [-1,-1]
            run_dvs[run_dv] = it
        nets = rst
        self.nets = nets
        self.nears = nears
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
        if nid not in self.pools:
            self.copy_forward(nid, model)
        if self.curr>=0:
            self.nears[self.curr][0] = nid
        self.curr = nid
        return self.fc_inputs_to(ins, self.gdv)
    def do_forward(self, fc):
        self.no_caches = True
        self.ctxs = {k:[] for k in self.nets}
        with torch.autograd.graph.saved_tensors_hooks(self.hook_pack, self.hook_unpack):
            rst = fc()
        return rst.to(self.gdv)
    def wrap_backward_deal(self, net_id):
        if self.backward_deal is None:
            return
        self.backward_deal(self.nets[net_id], self.opts[net_id])
    def hook_backward(self, model, grad_ins, grad_outs):
        nid = id(model)
        self.wrap_backward_deal(nid)
    def hook_pack(self, dt):
        if self.no_caches:
            # 不做缓存，数据不处理
            return -1, dt
        index = self.curr
        # forward时候为了后面计算梯度存的缓存，放到列表里方便转cpu和gpu
        self.ctxs[index].append(dt)
        return index, len(self.ctxs[index])-1
    def hook_unpack(self, x):
        nid = x[0]
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
