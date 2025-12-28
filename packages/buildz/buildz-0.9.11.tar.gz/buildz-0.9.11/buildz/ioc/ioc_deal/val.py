#
from ..ioc.base import Base, EncapeData
from buildz import xf
class ValDeal(Base):
    """
        数据val:
            {
                // 查找id，可选
                id: id
                type: val
                val|data: 任何数据
            }
        简写:
            [[val, id], data]
        极简:
            [val, data]

        例子:
            [val, 100元] // 字符串"100元"
        注: val是默认数据项的类型，如果data不是list或map，可以直接只写data：
            100元
    """
    def deal(self, edata:EncapeData):
        data = edata.data
        if type(data)==list:
            return data[-1]
        return xf.get_first(data, "val", "data")

pass
