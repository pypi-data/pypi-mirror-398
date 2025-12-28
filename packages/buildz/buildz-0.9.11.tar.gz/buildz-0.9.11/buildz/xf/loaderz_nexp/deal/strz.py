from .. import base
from .. import item
from .. import exp
from ... import file
from ... import code as codez
from . import lr

def init():
    cs = "abfnrtv\\'\"?0123456789xcde"
    maps = {k:k.encode()[0] for k in cs}
    global c2b
    c2b = maps
    global special_keys
    special_keys = [-1]*256
    s  = "abfnrtv\\'\""
    ts = b"\a\b\f\n\r\t\v\\\'\""
    for c,t in zip(s, ts):
        special_keys[c2b[c]] = t
    symbal_a = [False]*256
    for c in s:
        symbal_a[c2b[c]] = True
    global id_0,id_a,id_x,id_A
    global c2nums
    c2nums = [-1]*256
    id_0,id_a,id_A,id_x,id_u = b'0aAxu'
    for i in range(128):
        v = i-id_0
        if v>=0 and v<=9:
            c2nums[i] = v
            continue
        v = i-id_a
        if v>=0 and v<=5:
            c2nums[i]=v+10
            continue
        v = i-id_A
        if v>=0 and v<=5:
            c2nums[i]=v+10

pass
init()
def cs2num(bts, base, min, max, oct = False):
    cnt = 0
    rst = 0
    mv = 4
    if oct:
        mv = 3
    for i in range(max):
        if base+i>=len(bts):
            if i<min:
                return -1,0
            else:
                break
        bt = bts[base+i]
        v = c2nums[bt]
        if v<0 or (oct and v>9):
            if i<min:
                return -1,0
            else:
                break
        cnt+=1
        rst = (rst<<mv)|v
    return rst, cnt

pass
def decode_u(val):
    """
    1 byte: 7 0? 
    2 byte: 11 110? 10?
    3 byte: 16 1110? 10? 10?
    4 byte: 21 11110? 10? 10? 10?
    """
    if val<0x80:
        return [val]
    elif val<0x800:
        b0 = 0x80|(val&0x7f)
        b1 = 0x60|(val>>6)
        return [b1, b0]
    elif val<0x10000:
        b0 = 0x80|(val&0x3f)
        val>>=6
        b1 = 0x80|(val&0x3f)
        b2 = 0xe0|(val>>6)
        return [b2,b1,b0]
    else:
        b0 = 0x80|(val&0x3f)
        val>>=6
        b1 = 0x80|(val&0x3f)
        val>>=6
        b2 = 0x80|(val&0x3f)
        b3 = 0xf0|(val>>6)
        return [b3,b2,b1,b0]

pass
def translate_bts(bts, octs = None, hexs = None):
    i = 0
    rs = []
    while i<len(bts):
        c = bts[i]
        i+=1
        if c!=c2b['\\']:
            rs.append(c)
            continue
        x0 = bts[i]
        i+=1
        if special_keys[x0]>=0:
            rs.append(special_keys[x0])
            continue
        if x0==b'u'[0]:
            c_val, c_cnt = cs2num(bts, i, 4,4, 0)
            if c_cnt==0:
                raise Exception("\\uXXXX error")
            tmp = decode_u(c_val)
            i+=c_cnt
            rs+=tmp
            continue
        if x0==id_x:
            c_val, c_cnt = cs2num(bts, i, 2, 2, 0)
            if c_cnt==0:
                raise Exception("\\xXX error")
            if hexs is not None:
                tmp = hexs[c_val]
            else:
                tmp = [c_val]
            rs+=tmp
            i+=c_cnt
            continue
        c_val,c_cnt = cs2num(bts, i-1, 1, 3, 1)
        if c_cnt>0:
            if octs is not None:
                tmp = octs[c_val]
            else:
                tmp = [c_val%256]
            rs+=tmp
            i+=c_cnt-1
            continue
        rs.append(c)
        rs.append(x0)
        #i-=1
    return bytes(rs)

pass
def gen_chars(code="utf-8"):
    simple = "abfnrtv\\'\""
    octs = [0]*512
    hexs = [0]*256
    for i in range(512):
        if i<256:
            vhex = hex(i)[2:]
            if len(vhex)==1:
                vhex = "0"+vhex
            cmd = f"'\\x{vhex}'"
            hexs[i] = list(eval(cmd).encode(code))
        voct = oct(i)[2:]
        cmd = f"'\\{voct}'"
        octs[i] = list(eval(cmd).encode(code))
    return octs, hexs

pass
class PrevStrDeal(lr.LRDeal):
    def types(self):
        if not self.deal_build:
            return []
        return ['str']
    def build(self, obj):
        obj.is_val = 1
        if self.translate:
            val = obj.val
            val = self.do_translate(val)
            obj.val = val
        return obj
    def prepare(self, mg):
        super().prepare(mg)
        self.as_bytes = mg.as_bytes
        #if not self.as_bytes:
        #    self.octs,self.hexs = gen_chars()
        self.label_l2 = mg.like("\\")
        self.label_qt = mg.like('"')
        self.label_et = mg.like("\n")
        self.label_lr = mg.like("\r")
        self.label_nl = mg.like("")
        self.et_in_right = self.right.count(self.label_et)
    def init(self, left = '"', right= '"', single_line = False, note = False, translate = False, deal_build = False):
        super().init(left, right, 'str')
        self.single_line = single_line
        self.note = note
        self.translate = translate
        self.deal_build = deal_build
        self.as_bytes = True
        self.octs = None
        self.hexs = None
    def json_loads(self, s):
        import json
        x = s
        cd = None
        if type(x)==bytes:
            x, cd = file.decode_c(x)
        rs = json.loads(x)
        if type(s)==bytes:
            rs = rs.encode(cd)
        return rs
    def do_translate(self, s):
        """
            取巧用python的eval来生成字符表
        """
        is_bytes = type(s)==bytes
        if is_bytes:
            return codez.ubytes(s, "utf-8")
        else:
            return codez.ub2s(s.encode("utf-8"), "utf-8")
            return codez.ustr(s)
        if not is_bytes:
            s = s.encode("utf-8")
        #s = s.decode("unicode_escape")
        s = translate_bts(s, self.octs, self.hexs)
        if is_bytes:
            #s = s.encode("utf-8")
            s = s.decode("utf-8")
        return s
        """
            取巧直接调用json
        """
        qt = self.label_qt
        ql = self.label_l2
        et = self.label_et
        tr = self.label_lr
        nt = self.label_nl
        pt = ql+qt
        arr = s.split(pt)
        arr = [k.replace(qt, pt) for k in arr]
        s = pt.join(arr)
        #s = s.replace(qt, ql+qt)
        s = s.replace(tr, nt)
        arr = s.split(et)
        outs = [self.json_loads(qt+k+qt) for k in arr]
        outs = et.join(outs)
        return outs
    def deal(self, buffer, rst, mg):
        cl = buffer.read(self.ll)
        if cl != self.left:
            return False
        rm = buffer.full().strip()
        buffer.clean2read(self.ll)
        if len(rm)>0:
            if not self.note:
                raise Exception(f"unexcept char before string: {rm}")
            else:
                rst.append(item.Item(rm, type = "str", is_val = 0))
        tmp = cl[:0]
        ctmp = tmp[:0]
        do_judge = 1
        mark_et = 0
        mark_l2 = 0
        while True:
            if do_judge and self.right == buffer.rget(self.lr):
                break
            c = buffer.read_cache(1)
            if do_judge and c == self.label_et:
                mark_et += 1
            if len(c)==0:
                if self.single_line and self.note:
                    break
                raise Exception(f"unexcept string end while reading str")
            do_judge = 1
            if c == self.label_l2:
                mark_l2 = 1
                do_judge = 0
                c = buffer.read_cache(1)
                if len(c)==0:
                    raise Exception(f"unexcept string end while reading str")
        data = buffer.full()
        data = data[:-self.lr]
        buffer.clean()
        mark_et -= self.et_in_right
        if self.single_line and mark_et>0:
            print("left:",self.left, "right:", self.right)
            raise Exception(f"contain enter in single line string")
        if self.translate and mark_l2:
            data = self.do_translate(data)
        if self.note:
            return True
        rst.append(item.Item(data, type='str', is_val = 1))
        return True

pass
