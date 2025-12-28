#

from ..tools import *
from buildz.ioc import wrap
import json

try:
    import requests as rq
    session = rq.session()
except:
    rq = None
    session = None

pass
class Request(Base):
    def init(self, http_type, use_session, log, upd, cache=None, debug=False):
        self.type = http_type
        self.cache = cache
        self.use_session = use_session
        self.log = log.tag("Request")
        self.upd = upd
        self.fc = None
        self.fcs = None
        self.key_data = None
        self.debug = debug
        self.build()
    def build(self):
        fcs = {}
        global rq, session
        if rq is None:
            return
        obj = rq
        if self.use_session:
            obj = session
        fcs['get'] = [obj.get, "params"]
        fcs['post'] = [obj.post, "data"]
        fcs['json'] = [obj.post, "json"]
        fcs['put'] = [obj.put, "json"]
        fcs['delete'] = [obj.delete, 'json']
        self.fcs = fcs
        self.fc = self.fcs[self.type][0]
        self.key_data = self.fcs[self.type][1]
    def get_set(self, data, kd, maps, km):
        v = xf.get(data, kd)
        if v is not None:
            maps[km] = v
    def req(self, data):
        url = xf.g(data, url=None)
        maps = {}
        self.get_set(data, "data", maps, self.key_data)
        self.get_set(data, "cookies", maps, "cookies")
        self.get_set(data, "headers", maps, "headers")
        self.get_set(data, "proxies", maps, "proxies")
        return self.fc(url, **maps)
    def rsp(self, rp, data):
        url = xf.g(data, url=None)
        xf.s(data, status_code = rp.status_code)
        xf.s(data, result_code = rp.status_code)
        if self.debug:
            self.log.debug(f"request url '{url}' return code: {rp.status_code}")
        show_obj = None
        try:
            show_obj = rp.content
            xf.s(data, result_content=rp.content)
            debug_ct = rp.content
            s = xf.decode(rp.content, "utf-8")
            show_obj = s
            if self.debug:
                self.log.debug(f"request url '{url}' return msg:{s}")
            xf.s(data, result_text=s)
        except Exception as exp:
            self.log.warn(f"exp in deal response on '{url}': {exp}")
        try:
            obj = json.loads(s)
            show_obj = xf.dumps(obj,format=1,deepp=1)
            xf.s(data, result=obj)
        except Exception as exp:
            #self.log.warn(f"exp in deal response on '{url}': {exp}")
            pass
        if self.debug:
            self.log.debug(f"request '{url}' response: {show_obj}")
        try:
            xf.s(data, result_cookies=dict(rp.cookies))
        except Exception as exp:
            self.log.warn(f"exp in deal response on '{url}': {exp}")
        try:
            xf.s(data, result_headers = dict(rp.headers))
        except Exception as exp:
            self.log.warn(f"exp in deal response on '{url}': {exp}")
        return True
    def call(self, data, fc=None):
        if self.fc is None:
            self.log.error("install requests to use this(pip install requests)")
            return False
        if self.cache is not None:
            debug = self.cache.get("request.debug")
            if debug is not None:
                self.debug = debug
        if self.upd is not None:
            data = self.upd(data)
        url = xf.g(data, url=None)
        #self.log.debug(f"request.debug: {self.debug}")
        if self.debug:
            self.log.debug(f"try request url '{url}' with type {self.type}")
        try:
            rp = self.req(data)
        except Exception as exp:
            self.log.error(f"error in request '{url}' with method {self.type}: {exp}")
            return False
        self.rsp(rp, data)
        if fc is None:
            return True
        return fc(data)

pass


@wrap.obj(id="request.post")
@wrap.obj_args("post", "env, request.session, false", "ref, log", "ref, cache.modify", "ref, cache", "env, debug, false")
class Post(Request):
    pass

pass

@wrap.obj(id="request.json")
@wrap.obj_args("json", "env, request.session, false", "ref, log", "ref, cache.modify", "ref, cache", "env, debug, false")
class Json(Request):
    pass

pass

@wrap.obj(id="request.get")
@wrap.obj_args("get", "env, request.session, false", "ref, log", "ref, cache.modify", "ref, cache", "env, debug, false")
class Get(Request):
    pass

pass

@wrap.obj(id="request.put")
@wrap.obj_args("put", "env, request.session, false", "ref, log", "ref, cache.modify", "ref, cache", "env, debug, false")
class Put(Request):
    pass

pass

@wrap.obj(id="request.delete")
@wrap.obj_args("delete", "env, request.session, false", "ref, log", "ref, cache.modify", "ref, cache", "env, debug, false")
class Delete(Request):
    pass

pass
