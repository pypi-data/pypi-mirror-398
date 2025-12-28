#
from .. import xf
from .. import ioc
from ..base import Base
from ..ioc import wrap

@wrap.obj(id="list")
@wrap.obj_args("[ref, [env, buildz.auto.deal, auto.deal], [ref, autoz.deal]]", "[ioc, confs]")
class List(Base):
    def init(self, deal, mg):
        self.deal = deal
        self.curr_deal = deal
        self.mg = mg
    def curr(self):
        return self.curr_deal
    def call(self, maps, fp):
        datas = xf.g(maps, datas = [])
        sdeal = xf.g(maps, deal = None)
        deal_obj = xf.g(maps, deal_obj = None)
        deal = self.deal
        if deal_obj is not None:
            deal = deal_obj
        elif sdeal is not None:
            deal = self.mg.get(sdeal)
        self.curr_deal = deal
        for data in datas:
            if not deal(data):
                return False
        return True

pass
#wrap.add_datas("[(env, env.buildz.auto.deal), buildz.auto.deal, auto.deal]")
@wrap.obj_args("[env, buildz.auto.deal, auto.deal]")
@wrap.obj(id="autoz.deal")
class DfDeal(Base):
    def init(self, id):
        self.id = id
    def call(self, data):
        print(f"[ERROR] implement obj with id '{self.id}' by yourself")

pass



