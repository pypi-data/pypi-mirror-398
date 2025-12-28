from buildz import Base, xf, dz
from . import argz
from . import evalx
from ..iocz.ioc_deal.base import BaseEncape
class Fc(Base):
    def str(self):
        return str(self.fc)
    def init(self, fc=None):
        self.fc = fc
    def call(self, params):
        return self.fc(*params.args, **params.maps), 1
    @staticmethod
    def make(fc):
        if isinstance(fc, Fc):
            return fc
        return Fc(fc)
class RetFc(Fc):
    def call(self, params):
        return (params.args, params.maps), 1
def cal_eval(eval, inputs):
    if eval is None:
        return 1
    return eval(inputs)
def cal_args(args, inputs):
    if args is None:
        return inputs
    return args(inputs)
def deal_exp(fc, params, args):
    try:
        return fc(params)
    except argz.ArgExp as exp:
        if args is not None:
            exp = args.deal_exp(exp)
        raise exp
class Call(Fc):
    def str(self):
        return str(self.fcs)
    def init(self, fc, args=None, eval=None):
        if not dz.islist(fc):
            fc = [fc]
        fc = [self.make(k) for k in fc]
        self.fcs = fc
        self.args = args
        self.eval = eval
    def deal(self, params):
        rst = None,0
        for fc in self.fcs:
            val,mark_call = fc(params)
            if mark_call:
                rst = val, mark_call
        return rst
    def call(self, params):
        if not cal_eval(self.eval, params):
            return None, 0
        params = cal_args(self.args, params)
        return deal_exp(self.deal, params, self.args)
    def add(self, fc):
        self.fcs.append(self.make(fc))

pass