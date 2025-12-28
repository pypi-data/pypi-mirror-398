
from .base import *
from ..ioc.unit import Unit
class WrapFcs:
    def __init__(self, unit, fcs=None):
        if fcs is None:
            fcs = {}
        self.buildz_unit = unit
        self.buildz_fcs = fcs
    def __setitem__(self, key, val):
        self.buildz_fcs[key] = val
    def __getitem__(self, key):
        return self.buildz_fcs[key]
    def __getattr__(self, key):
        if key in self.buildz_fcs:
            return self.buildz_fcs[key]
class WrapUnit(Unit):
    def add_conf(self, conf, tag=None):
        if self.mg is None:
            self.tmp_confs.append([conf, tag])
        else:
            super().add_conf(conf, tag)
    def bind(self, mg):
        if self.mg == mg:
            return
        super().bind(mg)
        for conf, tag in self.tmp_confs:
            self.add_conf(conf, tag)
        self.tmp_confs = []
        for fc in self.binds:
            fc(mg)
        self.binds = []
    def init(self, ns=None, deal_ns = None, env_ns = None, units=None):
        super().init(ns, deal_ns, env_ns)
        self.units = None
        self.tmp_confs = []
        self.fcs = {}
        self.binds = []
        self.wrap = WrapFcs(self, self.fcs)
        self.bind_units(units)
    def add_bind(self, fc):
        if self.mg is not None:
            fc(self.mg)
        else:
            self.binds.append(fc)
    def bind_units(self, units):
        if self.units == units:
            return
        self.units = units
        units.clone_fcs(self)
    def set_fc(self, key, fc):
        fc.bind(self)
        self.wrap[key] = fc

pass
class WrapUnits(Base):
    def clone_fcs(self, unit):
        for key, fc in self.fcs.items():
            unit.set_fc(key, fc.clone(unit))
    def bind(self, mg):
        self.mg = mg
        for key, unit in self.units.items():
            unit.bind(mg)
    def init(self):
        self.units = {}
        self.mg = None
        self.fcs = {}
    def set_fc(self, key, fc):
        self.fcs[key] = fc
    def unit(self, ns=None, deal_ns = None, env_ns = None):
        key = (ns, deal_ns, env_ns)
        if key not in self.units:
            unit = WrapUnit(ns, deal_ns, env_ns, self)
            if self.mg is not None:
                unit.bind(self.mg)
            self.units[key] = unit
        return self.units[key]
    def call(self, *a,**b):
        return self.unit(*a,**b)