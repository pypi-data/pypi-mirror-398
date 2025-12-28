#


from .. import xf
from .. import ioc
from ..base import Base
from ..ioc import wrap
from ..tools import *
import time, sys
#from ..logz import FpLog
from .. import logz
@wrap.obj(id="log")
@wrap.obj_sets(cache="ref,cache")
class AutoLog(logz.Logs):
    def call(self, maps, fp):
        fp = xf.g(maps, log = None)
        fp = self.cache.rfp(fp)
        shows = xf.get(maps, "log.shows")
        if shows is None:
            shows = ["info", "warn", "error"]
        format = xf.get(maps, "log.format")
        #print(f"[TETSZ] format: {format}")
        fplog = logz.FpLog(fp,shows=shows,format=format)
        stdlog = logz.StdLog(shows=shows,format=format)
        self.init([fplog, stdlog], shows)
        return True

pass
