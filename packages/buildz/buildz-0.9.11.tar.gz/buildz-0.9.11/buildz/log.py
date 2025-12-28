#


from . import xf, ioc, fz, dz, path as pathx
from .base import Base
import time, sys, threading, os
class Check(Base):
    def str(self):
        return f"Check<self.whitelist: {self.whitelist}, self.blacklist: {self.blacklist}, self.default_pass: {self.default_pass}>"
    @staticmethod
    def build_conf(conf):
        whitelist, blacklist, default_pass, passes, rejects,default = dz.g(conf, whitelist=None, blacklist=None, default_pass=False, passes=[], rejects = [], default=False)
        default_pass = default_pass or default
        whitelist = whitelist or passes
        blacklist = blacklist or rejects
        return Check(whitelist, blacklist, default_pass)
    def init(self, whitelist=[], blacklist=[], default_pass=False):
        self.whitelist = set(whitelist)
        self.blacklist = set(blacklist)
        self.default_pass = default_pass
    def add_pass(self, tag):
        self.whitelist.add(tag)
        if tag in self.blacklist:
            self.blacklist.remove(tag)
    def remove_pass(self, tag):
        self.whitelist.remove(tag)
    def add_reject(self, tag):
        self.blacklist.add(tag)
        if tag in self.whitelist:
            self.whitelist.remove(tag)
    def remove_reject(self, tag):
        self.blacklist.remove(tag)
    def set_default(self, val):
        self.default_pass = val
    def call(self, tag):
        if tag in self.whitelist:
            return True
        if tag in self.blacklist:
            return False
        return self.default_pass
class Log(Base):
    '''
        日志的基类或壳，需要传入实际输出方法或者实现do_log方法
        提供方法接收参数生成日志格式字符串，然后调用实际输出方法或do_log
    '''
    def build_tags(self, conf):
        tags,shows = dz.g(conf, tags=None, shows=None)
        if tags is not None:
            tags = Check.build_conf(tags)
        if shows is not None:
            shows = Check.build_conf(shows)
        print(f"tags: {tags}")
        print(f"shows: {shows}")
        self.check_tags = tags or self.check_tags
        self.shows = shows or self.shows
        return self
    def show(self, type, on=True):
        if not on:
            return self.unshow(type)
        self.shows.add_pass(type)
    def unshow(self, type):
        self.shows.add_reject(type)
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
    def init(self, shows = None, tag= None, base = None, lock = False, check_tags=None):
        self.shows=shows
        self._tag = tag
        self.base = base
        self.check_tags = check_tags
        if lock:
            self.lock = threading.Lock()
        else:
            self.lock = None
    def log(self, level, tag, *args):
        if self.shows is not None and not self.shows(level):
            return
        if self.check_tags is not None and not self.check_tags(tag):
            return
        if self.lock is not None:
            with self.lock:
                return self.do_log(level, tag, *args)
        return self.do_log(level, tag, *args)
    def xlog(self, level, *args):
        if not self.show(level):
            return
        self.log(level, self.tag, *args)
    def do_log(self, level, tag, *args):
        if self.base is not None:
            return self.base.log(level, tag, *args)
        raise Exception("unimpl")
    def __getattr__(self, key):
        def fc(*args):
            self.log(key, self._tag, *args)
        return fc
    def clean(self):
        pass
    def done(self):
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
class FormatLog(Log):
    def init(self, shows =None, tag=None, format=None, base=None, lock = False, check_tags=None):
        if format is None:
            format = "[{LEVEL}] %Y-%m-%d %H:%M:%S [{tag}] {msg}\n"
        self.format=format
        super().init(shows, tag, base, lock, check_tags)
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
    @staticmethod
    def build(conf,dp=None):
        fp = dz.g(conf, fp=None)
        dp = dz.g(conf, dp=dp)
        if dp is not None:
            if type(dp)==str:
                dp = pathx.Path(dp)
            fp = dp(fp)
        reset = dz.g(conf, reset=False)
        log = FpLog(fp)
        if reset:
            log.clean()
        log.build_tags(conf)
        return log
    def init(self, fp = None,shows =None, tag=None, format=None, base=None, lock = False, check_tags=None):
        super().init(shows, tag, format, base, lock, check_tags)
        self.fp = fp
    def clean(self):
        fp = time.strftime(self.fp)
        fz.removes(fp)
    def output(self, msg):
        if self.fp is not None:
            fp = time.strftime(self.fp)
            fz.makefdir(fp)
            fz.write(msg.encode("utf-8"), fp, 'ab')

pass
class StdLog(FormatLog):
    @staticmethod
    def build(conf,*a,**b):
        log = StdLog()
        log.build_tags(conf)
        return log
    def output(self, msg):
        sys.stdout.write(msg)

pass
class Logs(Log):
    '''
    {
        type: logs
    }
    '''
    @staticmethod
    def build(conf, *a,**b):
        conf_logs = dz.g(conf, logs=[])
        if len(conf_logs) == 0:
            return StdLog.build(conf)
        logs = []
        for conf_log in conf_logs:
            logs.append(builds(conf_log))
        log = Logs(logs)
        log.build_tag(conf)
        return log
    def init(self, logs=[], shows = None, tag= None, lock = False, check_tags=None):
        super().init(shows, tag, lock=lock, check_tags=check_tags)
        self.logs = list(logs)
    def do_log(self, level, tag, *args):
        for _log in self.logs:
            _log.log(level, tag, *args)
    def done(self):
        for log in self.logs:
            log.done()
    def clean(self):
        for log in self.logs:
            log.clean()

pass
class Builds(Base):
    def init(self, default=None):
        self.fcs = {}
        self.default = default
    def addx(self, **maps):
        for k,v in maps.items():
            self.fcs[k] = v
    def add(self, key, fc):
        self.fcs[key] = fc
    def call(self, conf, type=None,*a,**b):
        if type is None:
            type = dz.g(conf, type=self.default)
        return self.fcs[type](conf,*a,**b)

pass
builds = Builds("logs")
builds.addx(file=FpLog.build)
builds.addx(std=StdLog.build)
builds.addx(logs=Logs.build)
build_conf = builds

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