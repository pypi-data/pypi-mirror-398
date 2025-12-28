#

from .. import xf
from .. import ioc
from ..base import Base
from ..ioc import wrap

class DeepFc(Base):
    def init(self, fcs, default = None):
        self.default = default
        self.fc = None
        self.next=None
        if len(fcs)>0:
            self.fc = fcs[0]
            self.next = DeepFc(fcs[1:], default)
    def call(self, data):
        if self.fc is None:
            return self.default
        return self.fc(data, self.next)

pass
@wrap.obj(id = "buildz.auto.deal.fill")
@wrap.obj_args("ioc, confs")
class Fill(Base):
    def init(self, mg):
        self.mg = mg
    def call(self, orders, default=None):
        if type(orders)==str:
            orders = xf.loads(orders)
        if type(orders)==str:
            orders = [orders]
        fcs = [self.mg.get(id) for id in orders]
        return DeepFc(fcs,default)

pass