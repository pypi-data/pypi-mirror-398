#


from . import xf, ioc, fz
from .base import Base
from .ioc import wrap
#from .tools import *
import time, sys, threading
ns = wrap.ns("buildz.logz")
@ns.obj(id="baseLog")
@ns.obj_args("ref, buildz.logz.shows, null", "ref, buildz.logz.tag, null", "ref, buildz.logz.base, null")
class Log(Base):
    def show(self, type, on=True):
        if not on:
            return self.unshow(type)
        if type not in self.shows:
            self.shows.append(type)
    def unshow(self, type):
        if type in self.shows:
            self.shows.remove(type)
    def call(self, _tag):
        return self.tag(_tag)
    def tag(self, _tag):
        if _tag is not None and type(_tag) != str:
            try:
                if not hasattr(_tag, "__name__"):
                    _tag = _tag.__class__
                _tag = _tag.__module__+"."+_tag.__name__
            except:
                _tag = str(_tag)
        base = self
        if self.base is not None:
            base = self.base
        log = Log(self.shows, _tag, base)
        return log
    def get_tag(self):
        return self._tag
    def init(self, shows = None, tag= None, base = None, lock = False):
        if shows is None:
            shows = ["info", "debug", "warn", "error"]
        self.shows=shows
        self._tag = tag
        self.base = base
        if lock:
            self.lock = threading.Lock()
        else:
            self.lock = None
    def log(self, level, tag, *args):
        if self.lock is not None:
            with self.lock:
                return self.do_log(level, tag, *args)
        return self.do_log(level, tag, *args)
    def xlog(self, level, *args):
        if level not in self.shows:
            return
        self.log(level, self.tag, *args)
    def do_log(self, level, tag, *args):
        if self.base is not None:
            return self.base.log(level, tag, *args)
        raise Exception("unimpl")
    def __getattr__(self, key):
        def fc(*args):
            if key not in self.shows:
                return
            self.log(key, self._tag, *args)
        return fc
    # def info(self, *args):
    #     if "info" not in self.shows:
    #         return
    #     self.log("info", self._tag, *args)
    # def warn(self, *args):
    #     if "warn" not in self.shows:
    #         return
    #     self.log("warn", self._tag, *args)
    # def debug(self, *args):
    #     if "debug" not in self.shows:
    #         return
    #     self.log("debug", self._tag, *args)
    # def error(self, *args):
    #     if "error" not in self.shows:
    #         return
    #     self.log("error", self._tag, *args)
    def clean(self):
        pass

pass
def replaces(s, *args):
    for i in range(0,len(args),2):
        k,v = args[i],args[i+1]
        s = s.replace(k,v)
    return s

pass
def mstr(s):
    if s is None or len(s)==0:
        return s
    return s[:1].upper()+s[1:].lower()
@ns.obj(id="formatLog")
@ns.obj_args("ref, buildz.logz.shows, null", "ref, buildz.logz.tag, null", "ref, buildz.logz.format, null")
class FormatLog(Log):
    def init(self, shows =None, tag=None, format=None, base=None, lock = False):
        if format is None:
            format = "[{LEVEL}] %Y-%m-%d %H:%M:%S [{tag}] {msg}\n"
        self.format=format
        super().init(shows, tag, base, lock)
    def output(self, msg):
        raise Exception("impl")
    def do_log(self, level, tag, *args):
        m_level = level.lower()
        u_level = level.upper()
        x_level = mstr(level)
        args = [str(k) for k in args]
        msg = " ".join(args)
        if tag is None:
            tag = "base"
        rst = time.strftime(self.format, time.localtime(time.time()))
        msg = replaces(rst, "{Level}", x_level, "{level}", m_level, "{LEVEL}", u_level, "{tag}", tag, "{msg}", msg)
        self.output(msg)
class FpLog(FormatLog):
    def init(self, fp = None,shows =None, tag=None, format=None, base=None, lock = False):
        super().init(shows, tag, format, base, lock)
        self.fp = fp
    def clean(self):
        fz.removes(self.fp)
    def output(self, msg):
        #sys.stdout.write(msg)
        if self.fp is not None:
            fp = time.strftime(self.fp)
            fz.makefdir(fp)
            fz.write(msg.encode("utf-8"), fp, 'ab')

pass
class StdLog(FormatLog):
    def output(self, msg):
        sys.stdout.write(msg)

pass
#wrap.decorator.add_datas()
wrap.ns.add_datas("[logs.list, refs], buildz\.logz\.item,", ns = "buildz.logz")
@ns.obj(id="logs")
@ns.obj_args("ref, logs.list, []", "ref, buildz.logz.shows,null", "ref, buildz.logz.tag, null")
class Logs(Log):
    def init(self, logs=[], shows = None, tag= None, lock = False):
        super().init(shows, tag, lock=lock)
        self.logs = list(logs)
    def do_log(self, level, tag, *args):
        for _log in self.logs:
            _log.log(level, tag, *args)
    def clean(self):
        for log in self.logs:
            log.clean()

pass
def simple(fp=None,std=True, shows=None, tag=None, format=None,lock=False):
    logs = []
    if fp is not None:
        logs.append(FpLog(fp,shows,tag,format,lock))
    if std:
        logs.append(StdLog(shows,tag,format,lock))
    return Logs(logs)

pass

def build(obj=None, shows=None, tag=None, format=None):
    if obj is None:
        return StdLog(shows, tag, format)
    return obj

pass
make=build