#coding=utf-8
from buildz import xf, argx, pyz, ioc
from ..test import Help as BaseHelp
from os.path import dirname, join
from ..test import text_sfx, args, maps
dp = dirname(dirname(__file__))
default_fp = join(dp, "res")
class Help(BaseHelp):
    def __init__(self, dp, fp):
        fp = join(dp, fp)
        self.text = xf.loads(xf.fread(fp))['text'+text_sfx]
        self.text = self.text.replace("{default}", default_fp)
    def deal(self):
        print(self.text)

pass