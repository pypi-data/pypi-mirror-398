
'''
单元测试注解
'''
from ..base import Base,fcBase
from .. import logz
import traceback
class UnitTest(Base):
    def init(self, log=None):
        self.tests = []
        self.log = logz.make(log)
        self.bind_log('info')
        self.bind_log('debug')
        self.bind_log('warn')
        self.bind_log('error')
    def bind_log(self, key):
        def call(*a,**b):
            return getattr(self.log, key)(*a,**b)
        setattr(self, key, call)
    def case(self, key):
        key = str(key)
        def f(fc):
            self.tests.append([key, fc])
            return fc
        return f
    def wrap_call(self, _key, fc, args=[], maps={}):
        bk_log = self.log
        log = self.log(_key)
        self.log = log
        log.info("    unit test case: ", _key)
        rst = None
        done = True
        try:
            rst = fc(*args, **maps)
        except Exception as exp:
            done = False
            import traceback
            log.error("    unit test exp: ", exp)
            log.error(traceback.format_exc())
        log.info("    done unit test case: ", _key)
        self.log = bk_log
        return rst, done
    def single(self, key, args=[], maps={}):
        for _key, fc in self.tests:
            if _key==key:
                return self.wrap_call(_key, fc, args, maps)[0]
    def call(self, key = None, args=[], maps={}):
        if key is None:
            key = ''
        rst = []
        self.log.info(f"start unit test on key: {key}")
        for _key, fc in self.tests:
            if _key.find(key)==0:
                rst, done = self.wrap_call(_key, fc, args, maps)
                if not done:
                    break

pass
def make_loop_check(fc):
    def call(dts, args=[]):
        for i in range(len(dts)):
            dt = dts[i]
            fc(dt, args+[i])
    return call
def build(*a,**b):
    return UnitTest(*a,**b)