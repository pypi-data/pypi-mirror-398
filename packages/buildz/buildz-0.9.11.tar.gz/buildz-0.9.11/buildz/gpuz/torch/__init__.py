#coding=utf-8

__version__="0.0.1"

__author__ = "Zzz, emails: 1174534295@qq.com, 1309458652@qq.com"
# 小号多

from .middle_cache import MiddleCache

# 下面的dict_middle也弃了，上面的MiddleCache写的更合理
from .dict_middle import DictCache, Fcs
#from .dict_middle import *
Dict = DictCache

'''
20250917
写好的是MiddleCache
暂时别用DictCache，没测过

20251016
测试发现，数据在内存和显存间传输消耗太多，显存不足用此代码未必能提升多少性能，还不如加显存，或者把模型改小，不建议用
'''