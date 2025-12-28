#coding=utf-8
from buildz.tools import *
from buildz.ioc import wrap
@wrap.obj(id="request")
@wrap.obj_args("ref, log", "ref, cache.modify")
class Req(Base):
    def init(self, log, upd):
        self.upd = upd
        self.log = log.tag("Test.Req")
    def call(self, data, fc=None):
        data = self.upd(data)
        self.log.debug(f"test data: {data}")
        if fc is not None:
            return fc(data)
        return True

pass
from buildz.auto import Run
from buildz.ioc.wrap import decorator
import sys
def test():
    #print(f"wrap: {xf.dumps(decorator(),format=1,deep=1)}")
    rst = Run(basedir="res")("data/test")
    print(f"rst: {rst}")

pass
pyz.lc(locals(), test)
