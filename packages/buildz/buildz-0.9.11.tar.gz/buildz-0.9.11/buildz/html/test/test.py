
from buildz.html import parse
from buildz.tools import *
fp = "demo.html"
s = fz.read(fp, "rb").decode("utf-8")

obj = parse(s)

# 可以进行多次查询调用，后一次查询在前一次的结果集里做查询
rst = obj.finds("(class,toplist1-tr_1MWDu)").finds("tag=a,target=_blank").data()
rst = obj.searchs("class,toplist1-tr_1MWDu").finds("(tag,a),(tag,a),(target,_blank)").data()
rst = obj.searchs("class,toplist1-tr_1MWDu").searchs("tag,a", "tag, a", "target, _blank").data()

print(f"search rst: {rst}")