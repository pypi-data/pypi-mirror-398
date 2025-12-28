
#
from ..ioc.unit import Unit
from ... import dz,xf
from ..ioc.datas import Datas
'''
id|namespace|ns:
deal_id|deal_ns: 
env_id|env_ns:
envs.pub|envs.pri|envs.ns|envs: {
    
}
confs.pub|confs.pri|confs.ns|confs: [

]
confs.pub|confs.pri|confs.ns|confs: {

}
builds: [
    
]

or

[
    ...
]
'''
def split2list(s, by=','):
    if s is None:
        return [s]
    if not dz.islist(s):
        s = s.split(by)
    return s
def join_nnull(by, *args):
    args = [k for k in args if k is not None and k!=""]
    return by.join(args)
    
def joins(prefix, suffix=None, by='.', split=","):
    prefix = split2list(prefix,split)
    suffix = split2list(suffix,split)
    rst = []
    for pfx in prefix:
        for sfx in suffix:
            rst.append(join_nnull(by, pfx, sfx))
    return rst


class ConfUnit(Unit):
    #key_ns = ('id', 'namespace', 'ns')
    key_ns = joins("id,namespace,ns")
    #key_deal_ns = "deal_id,deal_ns,deal_namespace".split(",")
    key_deal_ns = joins("deal", "id,ns,namespace", "_")
    #key_env_ns = "env_id,env_ns,env_namespace,profile_id,profile_ns,profile_namespace".split(",")
    key_env_ns = joins("env,profile", "id,ns,namespace", "_")
    #key_confs_pub = "confs.pub,confs".split(",")
    key_confs_pub = joins("confs,conf", "pub,")
    #key_confs_pri = "confs.pri,confs.prv".split(",")
    key_confs_pri = joins("confs,conf", "pri,prv")
    #key_confs_ns = "confs.ns,confs.namespace".split(",")
    key_confs_ns = joins("confs,conf", "ns,namespace")
    #key_envs_pub = "envs.pub,envs,profiles,profiles.pub".split(",")
    key_envs_pub = joins("envs,env,profiles,profile", "pub,Pub,P,")
    #key_envs_pri = "envs.pri,envs.prv,profiles.pri,profiles.prv".split(",")
    key_envs_pri = joins("envs,env,profiles,profile", "pri,prv,local,p,l")
    #key_envs_ns = "envs.ns,envs.namespace,profiles.ns,profiles.namespace".split(",")
    key_envs_ns = joins("envs,env,profiles,profile", "ns,namespace,n")
    #key_builds = "builds,build".split(",")
    key_builds = joins("builds,build")
    def init(self, conf, mg):
        if type(conf)==str:
            conf = xf.loads(conf)
        if dz.islist(conf):
            conf = {'confs': conf}
        ns = dz.get_one(conf, self.key_ns)
        deal_ns = dz.get_one(conf, self.key_deal_ns)
        env_ns = dz.get_one(conf, self.key_env_ns)
        super().init(ns, deal_ns, env_ns)
        self.tag_key = None
        self.bind(mg)
        self.load(conf)
    def load_confs(self, confs, tag=None):
        rst = []
        if dz.isdict(confs):
            for k,v in confs.items():
                self.conf_key.fill(v, k)
                rst.append(v)
            confs = rst
        for item in confs:
            self.add_conf(item, tag)
            # key,find = self.conf_key(item)
            # if find:
            #     self.set_conf(key, item, tag)
    def load_envs(self, envs, tag=None):
        for key, val in envs.items():
            self.set_env(key, val, tag)
    def load(self, conf):
        tags = [Datas.Key.Pub, Datas.Key.Ns, Datas.Key.Pri]
        keys = [self.key_confs_pub, self.key_confs_ns, self.key_confs_pri]
        for key, tag in zip(keys, tags):
            tag_confs = dz.get_one(conf, key, [])
            self.load_confs(tag_confs, tag)
        keys = [self.key_envs_pub, self.key_envs_ns, self.key_envs_pri]
        for key, tag in zip(keys, tags):
            tag_envs = dz.get_one(conf, key, {})
            self.load_envs(tag_envs, tag)
        builds = dz.get_one(conf, self.key_builds, [])
        for item in builds:
            self.add_build(item)

pass
