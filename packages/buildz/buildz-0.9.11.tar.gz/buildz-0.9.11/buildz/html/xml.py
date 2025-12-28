from html.parser import HTMLParser
from .. import xf
from ..base import Base
import re
class SearchResult(Base):
    def str(self):
        return str(self.arr)
    def init(self, arr):
        self.arr = arr
        self.size = len(arr)
    def run(self, fc_name, *a, **b):
        rst = []
        for it in self.arr:
            fc = getattr(it, fc_name)
            rst+=fc(*a,**b).data()
        return SearchResult(rst)
    def searchs(self, *args, **maps):
        return self.run("searchs", *args, **maps)
    def finds(self, s):
        return self.run("finds", s)
    def tags(self, _tag):
        return self.searchs(tag=_tag)
    def call(self):
        return self.data()
    def data(self):
        return self.arr
    def text(self):
        return [it.text for it in self.arr]
    def texts(self):
        return [it.texts for it in self.arr]
    def tag(self):
        return [it.tag for it in self.arr]
    def gkey(self, attrs, k):
        if k is None:
            return attrs
        if k in attrs:
            return attrs[k]
        return None
    def attrs(self, k=None):
        return [self.gkey(it.attrs,k) for it in self.arr]

pass
class HtmlTag:
    def data(self):
        return self.to_maps()
    def to_maps(self):
        nodes = [n.to_maps() for n in self.nodes]
        rst = {'tag': self.tag, 'attrs': self.attrs, 'texts': self.texts, 'text': self.text, 'nodes': nodes}
        return rst
    def __str__(self):
        return xf.dumps(self.to_maps())
    def __repr__(self):
        return self.__str__()
    def match(self, val, pt):
        tag = self.tag
        text = self.text
        texts = self.texts
        attrs = self.attrs
        if type(pt)==list:
            tp = pt[0]
            v = pt[1]
        else:
            tp = "="
            v = pt
        if val is None and tp not in ["eval", "exec"]:
            return False
        if tp == '>':
            return val>v
        elif tp == "<":
            return val<v
        elif tp == "=":
            return val == v
        elif tp == ">=":
            return val>=v
        elif tp=="<=":
            return val<=v
        elif tp == "re":
            return len(re.findall(v, val))>0
        elif tp == 'eval':
            return eval(v)
        elif tp == 'exec':
            exec(v)
            return self.val
        else:
            raise Exception(f"not impl match type: '{tp}'")
    def get(self, key):
        ks = key.split(".")
        v = ks[0]
        if not hasattr(self, v):
            return None
        obj = getattr(self, v)
        for k in ks[1:]:
            if type(obj)==dict:
                if k not in obj:
                    return None
                obj = obj[k]
            elif type(obj)==list:
                k = int(k)
                if k>=len(obj):
                    return None
                obj = obj[k]
            else:
                return None
        return obj
    def check(self, args, maps):
        arr = args+list(maps.items())
        for k,v in arr:
            if k == "$":
                if not self.match(None, ["eval", v]):
                    return False
            else:
                val = self.get(k)
                if not self.match(val, v):
                    return False
        return True
    def __init__(self, tag, attrs=None):
        self.tag = tag
        if attrs is None:
            attrs = {}
        self.attrs = attrs
        self.nodes = []
        self.text = None
        self.texts = []
    def _search(self, rst, args, maps):
        if self.check(args, maps):
            rst.append(self)
        for n in self.nodes:
            n._search(rst, args, maps)
    def searchs(self, *args, **maps):
        tmp = []
        for k in args:
            if type(k)!=list:
                k = xf.loads(k)
            tmp.append(k)
        rst = []
        self._search(rst, tmp, maps)
        return SearchResult(rst)
    def tags(self, _tag):
        return SearchResult(self.searchs(tag = _tag))
    def finds(self, s):
        rst = []
        args = []
        maps = {}
        dt = xf.loads(s)
        if type(dt)==list:
            args = dt
        else:
            maps = dt
        if len(args)==2 and type(args[0])!=list:
            args = [args]
        self._search(rst, args, maps)
        return SearchResult(rst)
    def add_node(self, node):
        self.nodes.append(node)
    def add_text(self, text):
        self.text = text
        self.texts.append(text)

pass

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = HtmlTag("document")
        self.stacks = [self.data]
    def handle_comment(self, data):
        "处理注释，< !-- -->之间的文本"
        pass
    def handle_startendtag(self, tag, attrs):
        "处理自己结束的标签，如< img />"
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)
        pass
    def handle_starttag(self, tag, attrs):
        "处理开始标签，比如< div>；这里的attrs获取到的是属性列表，属性以元组的方式展示"
        attrs = {k:v for k,v in attrs}
        tag = HtmlTag(tag, attrs)
        self.stacks[-1].add_node(tag)
        self.stacks.append(tag)
        #print(f"Encountered a {tag} start tag")
        #for attr, value in attrs:
        #    print(f"   {attr} = {value}")
    def handle_data(self, data):
        self.stacks[-1].add_text(data)
        "处理数据，标签之间的文本"
        #print(f"----handle data in tags: {data}")
    def handle_endtag(self, tag):
        self.stacks.pop(-1)
        "处理结束标签,比如< /div>"
        #print(f"Encountered a {tag} end tag")

pass

def parse(text):
    obj = MyHTMLParser()
    obj.feed(text)
    return obj.data

pass