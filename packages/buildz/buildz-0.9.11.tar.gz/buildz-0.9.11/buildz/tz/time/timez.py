import time
from ... import Base
from ...logz import FpLog
class Clock(Base):
    def default(self, cost, fc, rst, *a, **b):
        print(f"cost {cost} sec on fc")
    def init(self, fc=None, out_sec = False, show = True):
        if fc is None:
            fc = self.default
        self.fc = fc
        self.show = show
        self.out_sec = out_sec
    def call(self, fc):
        curr = time.time()
        def tfc(*a,**b):
            curr = time.time()
            rst = fc(*a,**b)
            cost = time.time()-curr
            if self.show:
                self.fc(cost, fc, rst, *a, **b)
            if self.out_sec:
                rst = [rst, cost]
            return rst
        return tfc

pass
clock = Clock
timecost = Clock
showcost = Clock()