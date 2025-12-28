#coding=utf-8
from ..ioc.base import Base, EncapeData,IOCError
from .base import FormatData,FormatDeal
from buildz import xf, pyz
import os
dp = os.path.dirname(__file__)
join = os.path.join
class DealDeal(FormatDeal):
    """
        扩展的好处是自定义格式，除了id,type和parent字段，其他字段可以自己加
        假设生成个test.Demo，构造函数只有一个字段val
        {
            id: test
            type: object
            source: test.Demo
            construct: {
                args: [
                    (val, 'demo')
                ]
            }
        }
        自己写个生成特定对象的处理类:
        配置文件1 def_demo.js:
        {
            datas:[
                {
                    id: obj.demo.deal
                    type: object
                    source: test.BuildDemo
                }
                {
                    id: demo.deal
                    type: deal
                    source: obj.demo.deal
                    target: demo.deal
                }
            ]
            //inits初始化
            inits: [
                demo.deal
            ]
        }
        配置文件2 demo.js:
        //只有datas的时候可以简写成只写datas列表里的数据
        [
            {
                id: test
                type: demo.deal
                val: "demo"
            }
        ]
        调用后会注册到conf的deal上，用于扩展deals配置
        deal字段deal:
            {
                id:id
                type: deal
                target: type
                source: id # 要求source实现了方法__call__(self, edata:EncapeData)
            }
        简写:
            [[deal, id], target, source]
            [deal, target, source]
        例:
            [deal, target, source] //
    """
    def init(self, fp_lists=None, fp_defaults=None):
        super().init("DealDeal", fp_lists, fp_defaults, join(dp, "conf", "deal_lists.js"), None)
    def deal(self, edata:EncapeData):
        data = edata.data
        data = self.fill(data)
        source = xf.g(data, source=None)
        if source is None:
            raise IOCError("not source in dealdeal")
        target = xf.g(data, target=None)
        if target is None:
            raise IOCError("not target in dealdeal")
        obj = edata.conf.get(source)
        if obj is None:
            raise IOCError("source object not found in dealdeal")
        targets = target
        if type(targets) != list:
            targets = [targets]
        for target in targets:
            edata.conf.set_deal(target, obj)
        return None

pass
