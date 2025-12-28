#coding=utf-8
from buildz import xf, argx, pyz, ioc
from buildz.ioc.ioc.conf import Conf
from ..test import Help as BaseHelp
from os.path import dirname, join
from ..test import text_sfx, args, maps, en
class Help(BaseHelp):
    def __init__(self, dp, fp):
        fp = join(dp, fp)
        self.helps = xf.loads(xf.fread(fp))
        self.text = self.helps['text'+text_sfx]
    def deal(self):
        self._deal()
        if en:
            print("remarks isn't fully translated into English yet.")
    def _deal(self):
        if xf.g(maps, doc=0):
            print(Conf.__doc__)
            return
        fp = argx.get(maps, ('f', 'file'))
        if fp is None:
            fp = ioc.default_deals
        deals = xf.g(xf.loads(xf.fread(fp)), deals=[])
        types = [f"{k['type']}({xf.g(k, note='???')})" for k in deals]
        deals = {k['type']:k for k in deals}
        notes = []
        stypes = ", ".join(types)
        self.text = self.text.replace("{items}",stypes)
        var = argx.get(maps, ('h', 'help'))
        if var == True:
            print(self.text)
            return
        if var not in deals:
            print(f"unknown type: {var}")
            return
        build = deals[var]['build']
        c = pyz.load(build)
        doc = c.__doc__
        if doc is None:
            doc = "没有注释"
        print(doc)
pass
