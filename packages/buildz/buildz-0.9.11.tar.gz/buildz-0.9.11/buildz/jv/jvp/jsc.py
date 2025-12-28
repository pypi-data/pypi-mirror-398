#
import re,sys
from buildz import fz, dz, xf, argx, pyz, Base
def rps_dct(s, **maps):
    for k,v in maps.items():
        s = s.replace(f"<{k}>", v)
    return s

def rps_lst(s, *args):
    for i in range(0, len(args), 2):
        k,v = args[i:i+2]
        s = s.replace(f"<{k}>", v)
    return s
pt_param = ""
def has_body(s):
    return s.find("(")>=0
fc_pt = r'((?:public|protected|private){0,1}(?:static|\s)*(?:\<\w+\>){0,1}\s*[\w\<\>\[\]]*)\s+([\w]+)\s*\(([^)]*)\)\s*((?:throws\s+[^\{\}\[\]\(\)\;]+){0,1})\s*\{'
def fetch_method(s):
    pt = fc_pt#r'((?:public|protected|private|static|\s)*[\w\<\>\[\]]*)\s+([\w]+)\s*\(([^)]*)\)\s*\{'
    _type, method, params, exp = [k.strip() for k in re.findall(pt, s)[0]]
    return _type, method, params,exp
def fetch_methods(s):
    pt = fc_pt#r'((?:public|protected|private|static|\s)*[\w\<\>\[\]]*)\s+([\w]+)\s*\(([^)]*)\)\s*\{'
    return re.findall(pt, s)
def fetch_methods_text(s, text):
    #print(f"fetch_methods_text:", s)
    s=s.strip()
    mark_def = s.find("(")>0
    if not mark_def:
        fcs = fetch_methods(text)
        fcs = [k for k in fcs if k[1]==s]
        assert len(fcs)>0, f"method not found: {s}"
        tmp = fcs#[0]
    else:
        tmp = [fetch_method(s)]
    #print("tmp:", tmp)
    return tmp, mark_def
    rst = list(tmp)+[mark_def]
    return rst
def fetch_method_text(s, text):
    fcs, mark_def = fetch_methods_text(s, text)
    rst = list(fcs[0])+[mark_def]
    return rst
def fetch_vals(s):
    rst = []
    if s is None:
        return rst
    quote = None
    ignore = False
    tmp = ''
    for c in s:
        if ignore:
            ignore = False
        elif c == '\\':
            ignore = True
        elif c =='"':
            if quote is None:
                quote = c
            elif quote==c:
                quote = None
        elif c == ',' and quote is None:
            rst.append(tmp.strip())
            tmp = ''
            continue
        tmp+=c
    tmp = tmp.strip()
    if len(tmp)>0:
        rst.append(tmp)
    return rst

def fetch_vars(s):
    rst = []
    if s is None:
        return rst
    quote = None
    count = 0
    ignore = False
    tmp = ''
    for c in s:
        if c =='<':
            count+=1
        elif c=='>':
            count-=1
        elif c == ',' and count==0:
            rst.append(tmp.strip())
            tmp = ''
            continue
        tmp+=c
    tmp = tmp.strip()
    if len(tmp)>0:
        rst.append(tmp)
    return rst


def fc(s, val):
    return s
class Deals(Base):
    def init(self):
        self.fcs = {}
    def add(self, key, fc):
        self.fcs[key] = fc
    def fetch(self, order):
        left = order.find("(")
        right = order.rfind(")")
        od, val = order, None
        if left>0:
            assert right>0
            od = order[:left]
            val = order[left+1:right]
        return od.strip(), val
    def call(self, arr, orders, text):
        if type(arr) not in (list, tuple):
            arr = [arr]
        if len(orders)==0:
            return arr, []
        od = orders.pop(0)
        od, val = self.fetch(od)
        arr, others = self.call(arr, orders, text)
        #print(f"[TESTZ] arr:", arr)
        fc = self.fcs[od]
        rst = []
        for s in arr:
            a,b = fc(s, val, text)
            rst+=a
            others +=b
            #rst+=fc(s, val, text)
        return rst, others
class DealCodes(Deals):
    def init(self, left="<<", right=">>", spt="||",define="||"):
        super().init()
        self.left = left
        self.right = right
        self.spt = spt
        self.define = define
    def update(self, s):
        left, right, spt, define= self.left, self.right, self.spt, self.define
        pt = f"{left}[\s\S]*?{right}"
        finds = re.findall(pt, s)
        text = s
        for find in finds:
            src = find
            #print(f"[MATCH]:", find)
            #continue
            find = find[len(left):-len(right)]
            if find.find(define)==0:
                find = find[len(define):]
                i = 0
                while find[i:i+len(define)]!=define:
                    i+=1
                while find[i:i+len(define)]==define:
                    i+=1
                i-=1
                spt = find[:i]
                find = find[i+len(define):]
                #print(f"[XXX] find after define:",find)
            arr = find.split(spt)
            orders = arr[:-1]
            arr = arr[-1:]
            rst, others = self(arr, orders, s)
            rst+=others
            rs = "\n".join(rst)
            s = s.replace(src, rs)
            spt = self.spt
        return s