#
from .base import *
from .datas import Datas
from .confs import Confs
from .encapes import Encapes
from ... import pyz

class Builds(Base):
    def init(self, unit):
        self.need_build = False
        self.jobs = []
        self.dones = []
        self.unit = unit
        self.builds = None
    def bind(self, builds):
        if self.builds == builds:
            return
        self.builds = builds
        self.builds.add(self)
    def add(self, conf):
        self.jobs.append(conf)
        self.need_build = True
        if self.builds is not None:
            self.builds.add(self)
    def build(self):
        if not self.need_build:
            return
        self.need_build = False
        for conf in self.jobs:
            if Confs.is_conf(conf):
                encape,c,u = self.unit.get_encape(conf, self.unit.ns, self.unit.id)
            elif isinstance(conf, Encape):
                encape = conf
            else:
                encape,c,u = self.unit.get_encape(conf, self.unit.ns, self.unit.id)
            encape()
            self.dones.append(conf)
        self.jobs = []
    def call(self):
        self.build()
class Buildset(Base):
    def init(self, mg):
        self.mg = mg
        self.need_build = False
        self.jobs = []
        self.dones = []
    def add(self, builds):
        if builds.need_build:
            self.jobs.append(builds)
            self.need_build = True
        builds.bind(self)
    def build(self):
        if not self.need_build:
            return
        self.need_build = False
        for builds in self.jobs:
            builds()
            self.dones.append(builds)
        self.jobs = []
        self.need_build = False
    def call(self):
        self.build()

pass