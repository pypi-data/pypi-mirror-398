from ..iocz.conf import conf
from .. import Base, xf, dz,pyz
from .callz import *
from ..iocz.ioc_deal.base import BaseEncape,BaseDeal
from ..iocz.conf.up import BaseConf
from .conf_argz import *
from .evalx import *
from .. import iocz
from . import argz
class EnvFc(Fc):
    def init(self, unit):
        super().init()
        self.unit = unit
    def call(self, params):
        self.unit.update_env(params.maps)
        return True,1
class ArgsCallEncape(BaseEncape):
    def init(self, fcs, args, eval, unit):
        super().init()
        self.fcs = fcs
        self.args = args
        self.eval = eval
        self.call_fc = None
        self.unit = unit
    def ref(self, key, unit):
        key = self.obj(key)
        if type(key)==str:
            rst, find = unit.get(key)
            assert find, f"fc not found: '{key}'"
            key=rst
        return key
    def call(self, params=None):
        if self.call_fc is None:
            fcs = [self.ref(fc, self.unit) for fc in self.fcs]
            self.call_fc = Call(fcs, self.args, self.eval)
        return self.call_fc
class IOCZVarCallEncape(BaseEncape):
    def init(self, fc, args, eval, unit):
        if not dz.islist(fc):
            fc = [fc]
        self.fcs = fc
        self.args = args
        self.eval = eval
        self.unit = unit
    def call(self, params=None,**maps):
        if params is None:
            params = iocz.Params()
        inputs = params.inputs
        if inputs is None:
            inputs = argz.Params()
        if not cal_eval(self.eval, inputs):
            return None
        inputs = cal_args(self.args, inputs)
        params.inputs = inputs
        return deal_exp(self.deal, params, self.args)
    def deal(self, params):
        with self.unit.push_vars(params.inputs.maps):
            val = None
            for fc in self.fcs:
                if type(fc)==str:
                    fc, _tag, find = self.unit.get_encape(fc)
                    assert find, f"fc '{fc}' not found"
                _val = fc(params)
                val = pyz.nnull(_val, val)
            return val
class ArgsCallDeal(BaseDeal):
    def init(self, fc=True, update_env = False, fc_encape=None):
        super().init()
        _conf = BaseConf()
        index=1
        self.fc = fc
        self.update_env = update_env
        if fc_encape is None:
            fc_encape = ArgsCallEncape
        self.fc_encape = fc_encape
        if fc:
            _conf.ikey(1, 'fc', 'fcs,calls,call'.split(','))
            _conf.ikey(2, 'eval', "judges,judge,evals".split(","))
            _conf.ikey(3, 'conf')
        else:
            _conf.ikey(2, 'eval', "judges,judge,evals".split(","))
            _conf.ikey(1, 'conf')
        self.update=_conf
        self.args_builder = FullArgsBuilder()
    def deal(self, conf, unit):
        conf_eval = dz.g(conf, eval=None)
        conf_args = dz.g(conf, conf=None)
        _eval = None
        if conf_eval is not None:
            _eval = evalBuilder.default_build(UnitBuild(unit))(conf_eval)
        _args = None
        if conf_args is not None:
            _args = self.args_builder(conf_args)
        if self.fc:
            fcs = dz.g(conf, fc=[])
            if type(fcs)==str:
                fcs = [fcs]
            fcs = [self.get_encape(fc, unit) for fc in fcs]
        else:
            if self.update_env:
                fcs = [EnvFc(unit)]
            else:
                fcs = [RetFc()]
        return self.fc_encape(fcs, _args, _eval, unit)
class RetArgsDeal(ArgsCallDeal):
    def init(self):
        super().init(False)
class UpdateEnvDeal(ArgsCallDeal):
    def init(self):
        super().init(False,True)

class IOCZVarCallDeal(ArgsCallDeal):
    def init(self):
        super().init(fc_encape=IOCZVarCallEncape)
confs = xf.loads(r"""
# confs.pri: {
#     deal_args: {
#         type=deal
#         src=buildz.argzx.conf_callz.ArgsCallDeal
#         call=1
#         deals=[call,fc]
#     }
# }
confs.pri: [
    (
        (deal, deal_ret)
        buildz.argz.conf_callz.RetArgsDeal
        1,
        [argz_ret,ret]
    )
    (
        (deal, deal_argz_env)
        buildz.argz.conf_callz.UpdateEnvDeal
        1,
        [argz_env,argz_envs]
    )
    (
        (deal, deal_args)
        buildz.argz.conf_callz.ArgsCallDeal
        1,
        [argz,argz_call,argz_fc]
    )
    (
        (deal, deal_var)
        buildz.argz.conf_callz.IOCZVarCallDeal
        1,
        [vargz, argz_var]
    )
]
builds: [deal_args, deal_ret, deal_argz_env, deal_var]
""")
class ConfBuilder(Base):
    def init(self, conf=None):
        mg = iocz.build(conf)
        mg.add_conf(confs)
        self.mg = mg
        for key in 'push_var,push_vars,pop_var,pop_vars,set_var,set_vars,get_var,unset_var,unset_vars'.split(","):
            setattr(self, key, getattr(mg,key))
    def adds(self, conf):
        if type(conf)==str:
            conf = xf.loads(conf)
        conf = {'confs': conf}
        self.mg.add_conf(conf)
    def add(self, conf):
        if type(conf)==str:
            conf = xf.loads(conf)
        conf = {'confs': [conf]}
        self.mg.add_conf(conf)
    def call(self, key, args=[], maps={}):
        params = argz.Params(args, maps)
        #p = iocz.Params(params=params)
        fc, find = self.mg.get(key)
        #rst, find = self.mg.get(key, params=p)
        assert find, f"key not found: '{key}'"
        return fc(params)[0]
        return rst[0]
    def get(self, key, args=[], maps={}, ns=None):
        inputs = argz.Params(args, maps)
        params = iocz.Params(inputs=inputs)
        obj, find = self.mg.get(key, params=params)
        assert find, f"key not found: '{key}'"
        return obj
