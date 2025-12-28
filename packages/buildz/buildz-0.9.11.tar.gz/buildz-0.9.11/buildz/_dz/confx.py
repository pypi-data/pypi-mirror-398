#

'''
简单的方便读取配置文件的类
没安全措施
每个Conf里有当前的数据conf，和数据是否存在exist
可以执行的操作:
读取，循环读取，修改，删除，修改和删除不会通知其他节点

push和pop操作(耗时高)
push修改当前conf的key
生成修改记录

pop的时候全改回来
因为没用到，暂时不实现，只保留接口和数据

gets可以获取多个key，返回队列
top(domain)回到根节点的domain下
call(domain)到当前节点的domain下，不存在或没有数据就报错

Conf包含数据：
conf: 实际数据
exist: 数据是否存在
domain: 根节点到当前节点的路径字符串
spt,spts: 分割字符串
src: 只读配置，默认为空
root: 根节点



'''

from . import mapz
from buildz import xf
from ..base import Base
import os
def dzkeys(key, spt):
    if key is None:
        return []
    elif type(key)==str:
        key = key.split(spt)
    elif type(key) not in (list, tuple):
        key = [key]
    return key

class Conf(Base):
    def len(self):
        return len(self.conf)
    def items(self, as_conf=True):
        rst = []
        for i in range(self.len()):
            rst.append(self.list(i, as_conf))
        return rst
    def list(self, i, as_conf=True):
        conf = self.conf[i]
        if as_conf:
            domain = self.domain+self.spt+str(i)
            val = conf
            src = self.src_list(i, as_conf)
            obj = self.root or self
            find = True
            conf = Conf(self.spt, self.spts, domain, obj, src, val, find)
        return conf
    def lhget(self, key, default=None, loop=-1):
        '''
            循环读取，直到读取到的不是字符串或loop==0或没有对应的key了
        '''
        a,b = self._hget(key, default)
        bak = a, b
        obj = self.root or self
        while b and type(a)==str and loop!=0:
            a,b = obj._hget(a, default)
            if b:
                bak = a,b
            loop-=1
        if loop>0:
            bak = a,b
        return bak
    def key(self, ks):
        return self.spt.join(ks)
    def src_list(self, i, as_conf = True):
        if self.src is None:
            return None
        if self.src.get_type()!=list:
            return None
        if self.src.len()<=i:
            return None
        return self.src.list(i, as_conf)
    def src_hget(self, key, default):
        if self.src is None:
            return default, 0
        return self.src.hget(key, default, loop)
    def src_dm(self, domain):
        if self.src is None:
            return None
        return self.src(domain,0)
    def src_top(self, domain):
        if self.src is None:
            return None
        return self.src.top(domain, 0)
    def lget(self, key, default=None, loop=-1):
        return self.lhget(key, default, loop)[0]
    def hget(self, key, default=None):
        '''
            最基本的读取方法
            先从conf拿，没有则从src拿
        '''
        val, find = default, 0
        keys = dzkeys(key, self.spt)
        if self.exist and type(self.conf)==dict:
            val, find = mapz.dget(self.conf, keys, default)
        if find:
            return val, find
        return self.src_hget(keys, default)
    def get(self, key, default=None):
        val = self.hget(key, default)[0]
        #print(f"get {key} = {val}")
        return val
    def has(self, key):
        return self.hget(key, None)[1]
    def remove(self, key):
        if not self.exist or type(self.conf)!=dict:
            return
        keys = dzkeys(key, self.spt)
        return mapz.dremove(self.conf, keys)
    def spts_ks(self, keys):
        '''
            一堆key组成的字符串拆分成key的列表
        '''
        keys = dzkeys(keys, self.spts)
        keys = [k.strip() if type(k) == str else k for k in keys]
        return keys
    def set(self, key, val):
        keys = dzkeys(key, self.spt)
        mapz.dset(self.conf, keys, val)
    def top(self, domain = None, loop=0):
        root = self.root or self
        if domain is not None:
            root = root(domain, loop)
        return root
    def l(self, domain=None, loop=-1):
        return self(domain,loop)
    def call(self, domain=None, loop=0):
        '''
            获取子域下的数据作为Conf
        '''
        if domain is None:
            return self.root or self
        val,find = self.hget(domain)
        src = self.src_dm(domain)
        if self.domain:
            domain = self.domain+self.spt+domain
        obj = self.root or self
        bak = domain, val, find, src
        while loop!=0 and find and type(val)==str:
            bak = domain, val, find, src
            val,find = obj.hget(domain)
            src = self.src_top(domain)
            loop-=1
        domain,val,find,src=bak
        return Conf(self.spt, self.spts, domain, obj, src, val, find)
    def val(self):
        return self.conf
    def get_type(self):
        return type(self.val())
    def has_val(self):
        return self.exist
    def get_conf(self):
        return self.conf
    def str(self):
        return str(self.get_conf())
    def init(self, spt='.', spts=',', domain=None, root = None, src = None, conf=None, exist=1):
        self.spt = spt
        self.spts = spts
        self.domain = domain
        self.root = root
        self.src = src
        if conf is None:
            conf = {}
        self.conf = conf
        self.exist = exist
        self.history = {}
    def clean(self):
        '''
            清空当前数据
        '''
        if self.get_type()!=dict:
            return
        for key in self.conf:
            del self.conf[key]
        return self
    def dkey(self, key):
        if self.domain:
            key = self.domain+self.spt+key
        return key
    def update(self, conf, flush = 1, replace=1, visit_list=0):
        if flush:
            conf = xf.flush_maps(conf, lambda x:x.split(self.spt) if type(x)==str else [x], visit_list)
        #print(f"update with {conf}")
        xf.fill(conf, self.conf, replace=replace)
        return self
    def push(self, key, value, flush = 1, update=0, clean_history = 0):
        assert 0
        return key
    def pop(self, key, clean_history = 0):
        assert 0
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
    def g(self, **maps):
        rst = [self.get(k, v) for k,v in maps.items()]
        if len(rst)==1:
            rst = rst[0]
        return rst
    def s(self, **maps):
        [self.set(k,v) for k,v in maps.items()]
    def has_all(self, keys):
        keys = self.spts_ks(keys)
        rst = [1-self.has(key) for key in keys]
        return sum(rst)==0
    def has_any(self, keys):
        keys = self.spts_ks(keys)
        for key in keys:
            if self.has(key):
                return True
        return False
    @staticmethod
    def fcs_bind(fn, wfn, align=False, null_default= False):
        def wfc(self, keys, *objs, **maps):
            #print(f"[[[[[]]]]]{wfn} call by {id(self)}")
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
        setattr(Conf, wfn, wfc)

pass
maps = xf.loads(r"""
(get,0,1)
(lget,0,1)
(set,1)
(remove)
(push,1)
""")
for item in maps:
    k = item[0]
    ks = k+"s"
    item = item[:1]+[ks]+item[1:]
    Conf.fcs_bind(*item)

pass