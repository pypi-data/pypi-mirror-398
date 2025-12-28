#

from .ioc import confs
from .ioc.confs import ConfsList, Confs
from .ioc_deal.base import default_deals
from . import wrap
def build(fp_init = None, add_default_deals = True, add_wrap = True):
    obj = confs.Confs()
    if (fp_init is not None):
        if type(fp_init)==dict:
            obj.init(fp_init)
        else:
            obj.init_fp(fp_init)
    if add_default_deals:
        obj.add_fp(default_deals)
    if add_wrap:
        obj.add_decorator()
    return obj

pass