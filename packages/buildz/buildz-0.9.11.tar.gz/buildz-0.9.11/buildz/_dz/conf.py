
from . import mapz
from buildz import xf
from ..base import Base
import os
def dzkeys(key, spt):
    if key is None:
        return []
    # return mapz.keys(key, spt)
    if type(key)==str:
        key = key.split(spt)
    if type(key) not in (list, tuple):
        key = [key]
    return key

class BindKey(Base):
    def sub(self, key):
        return BindKey(key, False, self, self.obj)
    def init(self, key, abs=True, up=None, conf=None):
        self.key = key
        self.abs = abs
        self.spt = spt
        self.up = up
        self.obj = conf
    def bind(self, conf):
        self.obj=conf
    def get(self, conf=None, default=None):
        conf = self.conf(conf)
        if self.up:
            conf = self.up(conf)
        elif self.abs:
            conf = conf()
        return conf.get(self.key, default)
    def conf(self, obj):
        obj = obj or self.obj
        assert obj is not None
        return obj
    def set(self, val, conf=None):
        conf = self.conf(conf)
        if self.up:
            conf = self.up(conf)
        elif self.abs:
            conf = conf()
        return conf.set(self.key, val)
    def call(self, conf):
        conf = self.conf(conf)
        if self.up:
            conf = self.up(conf)
        elif self.abs:
            conf = conf()
        return conf(self.key)

pass
'''

实际数据：
src: Conf对象，最底层，只读
conf: dict数据，实际数据，可读可写
history: dict里是list，每个key在push前，把当前key对应的数据存入history中，后面pop的时候，删除当前数据，把之前的数据重新更新
_links: link对象，搜索方式是搜最长的有link的节点，返回link目标key拼接剩余key作为key的取值
link对象：[{子集}, 当前节点link目标, 是否有link(1是，0否)]，初始化为[{}, None, 0]


'''
class Conf(Base):
    @staticmethod
    def bind_key(key, abs=True, up = None):
        return BindKey(key, abs, up)
    def val(self):
        return self.get_conf()
    def get_type(self):
        return type(self.val())
    def has_val(self):
        obj = self.root or self
        return obj.has(self.domain)
    def top(self, domain = None, loop=0, link=0):
        root = self.root or self
        if domain is not None:
            root = root(domain, loop, link)
        return root
    def ltop(self, domain=None, loop=-1,link=0):
        return self.top(domain,loop,link)
        # return self.root or self
    def get_conf(self):
        if self.domain:
            key = self.domain
        obj = self.root or self
        if self.domain:
            return obj._get(self.domain)
        return obj.conf
    def str(self):
        return str(self.get_conf())
    def l(self, domain=None, loop=-1,link=0):
        return self(domain,loop,link)
    def call(self, domain=None, loop=0, link=0):
        if domain is None:
            return self.top()
        if self.domain:
            domain = self.domain+self.spt+domain
        obj = self.root or self
        if loop!=0:
            val, find = obj.hget(domain,link=link)
            while loop!=0 and find and type(val)==str:
                domain = val
                val,find = obj.hget(domain,link=link)
                loop-=1
        return Conf(self.spt, self.spts, domain, obj)
    def init(self, spt='.', spts=',', domain=None, root = None, src = None):
        self.spt = spt
        self.spts = spts
        self.domain = domain
        self.root = root
        self.src = src
        if root is None:
            self.conf = {}
            self.history = {}
            self._links = [{},None,0]
        self.dr_bind('_get', 'get')
        self.dr_bind('_hget', 'hget')
        self.dr_bind('_lget', 'lget')
        self.dr_bind('_lhget', 'lhget')
        self.dr_bind('_set', 'set')
        self.dr_bind('_has', 'has')
        self.dr_bind('_remove', 'remove')
        self.dr_bind('_link', 'link')
        self.dr_bind('_unlink', 'unlink')
        self.dr_bind('_push', 'push')
        self.dr_bind('_pop', 'pop')
        self.dr_bind('_stack_set', 'stack_set')
        self.dr_bind('_stack_unset', 'stack_unset')
        self.fcs_bind('get', 'gets', False, True)
        self.fcs_bind('lget', 'lgets', False, True)
        self.fcs_bind('set', 'sets', True)
        self.fcs_bind('remove', 'removes')
        self.fcs_bind('push', 'pushs', True)
        #self.fcs_bind('pop', 'pops')
        self.fcs_bind('stack_set', 'stack_sets', True)
        self.fcs_bind('stack_unset', 'stack_unsets')
        self.fcs_bind('link', 'links', True)
        self.fcs_bind('unlink', 'unlinks')
        for name,rename in zip("stack_set,stack_unset,stack_sets,stack_unsets".split(","), "tmp_set,tmp_unset,tmp_sets,tmp_unsets".split(',')):
            setattr(self, rename, getattr(self, name))
        self.have_all = self.has_all
    def clean(self):
        obj = self.root or self
        obj.conf = {}
        obj.history = {}
        obj._links = [{}, None, 0]
        return self
    def dkey(self, key):
        if self.domain:
            key = self.domain+self.spt+key
        return key
    def update(self, conf, flush = 1, replace=1, visit_list=0):
        if self.domain:
            ks = dzkeys(self.domain, self.spt)
            tmp = {}
            mapz.dset(tmp, ks, conf)
            conf = tmp
        if self.root:
            return self.root.update(conf, flush, replace, visit_list)
        if flush:
            conf = xf.flush_maps(conf, lambda x:x.split(self.spt) if type(x)==str else [x], visit_list)
        xf.fill(conf, self.conf, replace=replace)
        return self
    def dr_bind(self, fn, wfn):
        def wfc(key,*a,**b):
            key = self.dkey(key)
            obj = self.root or self
            fc = getattr(obj, fn)
            return fc(key, *a, **b)
        setattr(self, wfn, wfc)
    def fcs_bind(self, fn, wfn, align=False, null_default= False):
        def wfc(keys, *objs, **maps):
            keys = self.spts_ks(keys)
            fc = getattr(self, fn)
            rst = []
            for i in range(len(keys)):
                if i<len(objs):
                    val = fc(keys[i], objs[i], **maps)
                else:
                    if align:
                        raise Exception(f"not val[{i}]")
                    if null_default:
                        val = fc(keys[i], None, **maps)
                    else:
                        val = fc(keys[i], **maps)
                rst.append(val)
            return rst
        setattr(self, wfn, wfc)
    def _stack_set(self, key, value, flush = 1, update=0):
        return self._push(key, value, flush, update, 1)
    def _stack_unset(self, key):
        return self._pop(key, 1)
    def _push(self, key, value, flush = 1, update=0, clean_history = 0):
        keys = dzkeys(key, self.spt)
        val, find = mapz.dget(self.conf, keys)
        val = mapz.deep_clone(val)
        if clean_history or key not in self.history:
            self.history[key] = []
        self.history[key].append([val, find, update])
        if flush and type(value)==dict:
            value = xf.flush_maps(value, lambda x:x.split(self.spt) if type(x)==str else [x], 0)
        if type(value)==dict and update:
            self(key).update(value,flush=0)
        else:
            self._set(key, value)
    def _pop(self, key, clean_history = 0):
        if key not in self.history:
            return False
        lst = self.history[key]
        if len(lst)==0:
            return False
        rst = lst.pop(-1)
        if clean_history:
            self.history[key] = []
        if not rst[1]:
            self._remove(key)
            return True
        self._set(key, rst[0])
        return True
    def pops(self, keys, *a, **b):
        keys = self.spts_ks(keys)
        keys.reverse()
        for key in keys:
            self.pop(key)
    def with_push(self, key, *a, **b):
        self.push(key, *a, **b)
        def out():
            self.pop(key)
        return pyz.with_out(out)
    def with_pushs(self, keys, *a, **b):
        self.pushs(keys, *a, **b)
        def out():
            self.pops(keys)
        return pyz.with_out(out)
    def ld_get(self, obj, key, fc_init=None):
        keys = dzkeys(key, self.spt)
        for key in keys:
            if key not in obj[0]:
                if fc_init is None:
                    return None
                obj[0][key] = fc_init()
            obj = obj[0][key]
        return obj
    def ld_visit(self, obj, key, fc):
        keys = dzkeys(key, self.spt)
        deep = 0
        fc(obj, deep, len(keys))
        for key in keys:
            if key not in obj[0]:
                break
            deep+=1
            obj = obj[0][key]
            fc(obj, deep, len(keys))
    def _link(self, src, target):
        #print(f"[LINK] {src}->{target}")
        links = self.ld_get(self._links, src, lambda :[{}, None, 0])
        links[1] = target
        links[2] =1
    def _unlink(self, key):
        links = self.ld_get(self._links, key)
        if links is None:
            return False
        links[1] = None
        links[2] = 0
        return True
    def link_match(self, keys):
        obj = self.root or self
        rst = [[None,0,0]]
        def fc_match(val, deep, size):
            if not val[2]:
                return
            rst[0] = val[1], val[2], deep
        self.ld_visit(obj._links, keys, fc_match)
        return rst[0]
    def _set(self, key, val):
        keys = dzkeys(key, self.spt)
        mapz.dset(self.conf, keys, val)
    def _lhget(self, key, default=None, loop=-1, link=-1):
        a,b = self._hget(key, default, link)
        bak = a, b
        while b and type(a)==str and loop!=0:
            a,b = self._hget(a, default, link)
            if b:
                bak = a,b
            loop-=1
        return bak
    def key(self, ks):
        return self.spt.join(ks)
    def src_hget(self, key, default, link=-1):
        if self.src is None:
            return default, 0
        return self.src.hget(key, default, loop, link)
    def _lget(self, key, default=None, loop=-1, link=-1):
        return self._lhget(key, default, loop, link)[0]
    def _hget(self, key, default=None, link=-1):
        #print(f"_hget: {key}, {default}, {link}")
        keys = dzkeys(key, self.spt)
        val, find = mapz.dget(self.conf, keys, default)
        if find or link==0:
            if not find:
                val, find = self.src_hget(key, default, link)
            return val, find
        lnk, has_lnk, deep = self.link_match(keys)
        if not has_lnk:
            return self.src_hget(key, default, link)
            #return val, find
        keys = keys[deep:]
        key = self.spt.join(keys)
        if lnk is not None:
            key = lnk+self.spt+key
        if link>0:
            link-=1
        return self._hget(key, default, link)
    def _get(self, key, default=None, link=-1):
        return self._hget(key, default,link)[0]
        keys = dzkeys(key, self.spt)
        return mapz.dget(self.conf, keys, default)[0]
    def _remove(self, key):
        # TODO
        keys = dzkeys(key, self.spt)
        return mapz.dremove(self.conf, keys)
    def _has(self, key, link=-1):
        return self._hget(key, None, link)[1]
        keys = dzkeys(key, self.spt)
        return mapz.dhas(self.conf, keys)
    def spts_ks(self, keys):
        keys = dzkeys(keys, self.spts)
        keys = [k.strip() if type(k) == str else k for k in keys]
        return keys
    def g(self, **maps):
        rst = [self.get(k, v) for k,v in maps.items()]
        if len(rst)==1:
            rst = rst[0]
        return rst
    def s(self, **maps):
        [self.set(k,v) for k,v in maps.items()]
    def has_all(self, keys, link = -1):
        keys = self.spts_ks(keys)
        rst = [1-self.has(key, link) for key in keys]
        return sum(rst)==0
    def has_any(self, keys, link=0):
        keys = self.spts_ks(keys)
        for key in keys:
            if self.has(key, link):
                return True
        return False

pass

class ArgsConf(Base):
    def init(self, conf, args):
        self.conf =conf
        self.args =args
    def __getattr__(self, key):
        return getattr(self.conf,key)

pass