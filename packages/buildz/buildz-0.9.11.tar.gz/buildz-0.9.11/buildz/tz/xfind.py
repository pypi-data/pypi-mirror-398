from .. import xf
from ..base import Base
import re

def default_update(node, args, up):
    """
        默认args是patterns, deep形式
    """
    deep = args[1]
    if deep == 0:
        return None
    if deep>0:
        deep -= 1
    return [args[0], deep]

pass
class DefaultSearch:
    """
        默认args是patterns, deep形式
        patterns:
        [or, [re, key, 'a.*'], ['=', key, ]]
    """
    def __init__(self):
        self.opts = {}
        self.opts['or'] = self.fc_or
        self.opts['and'] = self.fc_and
        self.opts['not'] = self.fc_not
        self.opts['xor'] = self.fc_xor
        self.sets(("=", "eq"), self.make_logic(lambda data, val:data==val))
        self.sets((">", "bg"), self.make_logic(lambda data, val:data>val))
        self.sets((">=", "be"), self.make_logic(lambda data, val:data>=val))
        self.sets(("<", "lt"), self.make_logic(lambda data, val:data<val))
        self.sets(("<=", "le"), self.make_logic(lambda data, val:data<=val))
        self.sets("in", self.make_logic(lambda data, val:data in val))
        self.sets("re", self.make_logic(lambda data, val:len(re.findall(val, str(data)))>0))
        self.sets(["$", "eval"], self.fc_eval)
        self.sets(["*", "exec"], self.fc_exec)
        self.sets("mkv", self.fc_mkv)
    def fc_eval(self, node, args, curr):
        cmd = args[0]
        return eval(cmd)
    def fc_exec(self, node, args, curr):
        """
            exec(cmd)
            return self.rst
        """
        cmd = args[0]
        exec(cmd)
        return self.rst
    def sets(self, keys, fc):
        if type(keys) not in (list, tuple):
            keys = [keys]
        for k in keys:
            self.opts[k] = fc
    def fc_mkv(self, node, args, curr):
        data = node.data
        if type(data)!=dict:
            return False
        key = args[0]
        val = args[1]
        if key not in data:
            return False
        return data[key].to_data()==val
    @staticmethod
    def fetch_judge_by(judge_by, node, curr):
        #print(f"[TESTZ] fetch_judge_by: {judge_by}, {node}, {curr}")
        if judge_by in ('key', 'k'):
            if curr is None:
                return None, False
            key = curr[0]
            return key,True
        elif judge_by in ('index', 'i'):
            if curr is None:
                return None, False
            key = curr[0]
            return int(key),True
        elif judge_by in ('value', 'val', 'v'):
            return node.to_data(),True
        else:
            assert False, f"unsupport judge_by: {judge_by}"
    def make_logic(self, fc):
        def check(node, args, curr):
            judge_by = args[0]
            data, get = self.fetch_judge_by(judge_by, node, curr)
            if not get:
                return False
            val = args[1]
            return fc(data, val)
        return check
    def fc_xor(self, node, args, curr):
        a = self.fc(node, args[0], curr)
        b = self.fc(node, args[1], curr)
        return a^b
    def fc_not(self, node, args, curr):
        return not self.fc(node, args[0], curr)
    def fc_or(self, node, args, curr):
        for pattern in args:
            if self.fc(node, pattern, curr):
                return True
        return False
    def fc_and(self, node, args, curr):
        for pattern in args:
            if not self.fc(node, pattern, curr):
                return False
        return True
    def fc(self, node, args, curr):
        opt = args[0]
        #print(f"[TESTZ] opt: {opt}, {type(opt)}, args: {args}")
        assert opt in self.opts, f"unkonwn opt {opt} in {list(self.opts.keys())}"
        return self.opts[opt](node, args[1:], curr)
    def __call__(self, node, args, curr):
        args = args[0]
        jg = self.fc(node, args, curr)
        if not jg:
            return []
        return [[curr, node]]

pass
default_search = DefaultSearch()
class SearchArray(Base):
    @staticmethod
    def parse(data):
        return SearchArray.single(Node.parse(data))
    @staticmethod
    def single(data):
        return SearchArray([[None, data]])
    def str(self):
        return str(self.arr)
    def init(self, arr):
        self.arr = arr
        self.size = len(arr)
    def expand(self, ks):
        if ks is None:
            return []
        return self.expand(ks[1]) + [ks[0]]
    def datas(self):
        rst = [[self.expand(ks), nd.to_data()] for ks, nd in self.arr]
        return rst
    def vals(self):
        rst = [nd.to_data() for ks, nd in self.arr]
        return rst
    def keys(self):
        rst = [self.expand(ks) for ks, nd in self.arr]
        return rst
    def searchs(self, args):
        """
            array.searchs((patterns, fc_search, fc_update), (patterns, fc_search, fc_update), ...)
        """
        rst = self.arr
        for patterns, fc_search, fc_update in args:
            tmp = []
            for ks, node in rst:
                tmp += node.search(patterns, fc_search, fc_update, ks)
            rst = tmp
        return SearchArray(rst)
    def searchs_fc(self, args, fc_search=None, fc_update=None):
        rst = self.arr
        if type(args)==str:
            args = xf.loads(args)
        for patterns in args:
            tmp = []
            for ks, node in rst:
                tmp += node.search(patterns, fc_search, fc_update, ks)
            rst = tmp
        return SearchArray(rst)
    def searchs_dfc(self, args, deep=-1, fc_search=None, fc_update=None):
        rst = self.arr
        if type(args)==str:
            args = xf.loads(args)
        for patterns in args:
            tmp = []
            for ks, node in rst:
                tmp += node.search([patterns,deep], fc_search, fc_update, ks)
            rst = tmp
        return SearchArray(rst)

pass
class Node:
    @staticmethod
    def parse(data):
        if type(data)==list:
            rst = [Node.parse(it) for it in data]
        elif type(data)==dict:
            rst = {k:Node.parse(v) for k,v in data.items()}
        else:
            rst = data
        return Node(rst)
    def to_data(self):
        if type(self.data)==list:
            rst = [it.to_data() for it in self.data]
        elif type(self.data)==dict:
            rst = {k:v.to_data() for k,v in self.data.items()}
        else:
            rst = self.data
        return rst
    def __str__(self):
        return xf.dumps(self.to_data())
    def __repr__(self):
        return self.__str__()
    def __init__(self, data):
        self.data = data
    def search(self, args, fc_search=None, fc_update = None, curr = None):
        """
            args: 匹配条件
            返回:
                SearchArray(rst)
                rst: [
                    [keys, val],
                    ...
                ]
            SearchArray(node).searchs(...)
        """
        if fc_update is None:
            fc_update = default_update
        if fc_search is None:
            fc_search = default_search
        args = fc_update(self, args, curr)
        if args is None:
            return []
        rst = fc_search(self, args, curr)
        if type(self.data)==list:
            for i in range(len(self.data)):
                it = self.data[i]
                crr = [i, curr]
                rst += it.search(args, fc_search, fc_update, crr)
        elif type(self.data)==dict:
            for k,v in self.data.items():
                crr = [k, curr]
                rst += v.search(args, fc_search, fc_update, crr)
        return rst

pass
