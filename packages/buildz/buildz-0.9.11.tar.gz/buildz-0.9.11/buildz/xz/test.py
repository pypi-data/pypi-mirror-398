#

from buildz.xz import trs
from buildz import xf

data = xf.loadf("data.js")
conf = xf.loadf("conf.js")

obj = trs.Translate(conf, inline = 1, remove_src = 1, vars = {"x":"test"})
rst = obj(data)
print(rst)

