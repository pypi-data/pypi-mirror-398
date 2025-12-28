

from buildz.tools import *
from buildz import tz, argx, dz
import os
join = os.path.join
import struct
r'''
python -m buildz.tz.filediff diff src_dp target_dp diff_file
比较src_dp和target_dp的差异，把target_dp新增的内容记录到diff_file中

python -m buildz.tz.filediff recover src_dp target_dp diff_file
根据diff_file和src_dp，将新增的文件和修改过内容的文件添加到target_dp中（没改过的不会添加）
'''
def diff(fp1, fp2):
    bs1 = fz.read(fp1).decode("utf-8")
    bs2 = fz.read(fp2).decode("utf-8")
    stps = tz.m_steps(bs1, bs2,split=0)
    return tz.m_encode(stps)
def diffs(dp1, dp2):
    fps1 = set(fz.search(dp1, relative=1))
    fps2 = set(fz.search(dp2, relative=1))
    fps = set(fps1)
    fps.update(fps2)
    rst = []
    for fp in fps:
        if fp in fps1 and fp in fps2:
            fp1 = join(dp1, fp)
            fp2 = join(dp2, fp)
            h1 = fz.fhash(fp1)
            h2 = fz.fhash(fp2)
            if h1!=h2:
                rst.append(['ne', fp, diff(fp1, fp2)])
            pass
        elif fp in fps1:
            rst.append(['del', fp])
        else:
            rst.append(['add', fp, fz.read(join(dp2, fp))])
    return rst
tps = 'ne,del,add'.split(",")
btps = b'n,d,a'.split(b",")
itps = {}
for i in range(3):
    itps[tps[i]] = i
    itps[btps[i]] = i
def rst2bts(rst):
    n = len(rst)
    bs = b''
    bn = struct.pack(">H", n)
    bs = bn
    for it in rst:
        tp,fp=it[:2]
        btp = btps[itps[tp]]
        bfp = bytes([len(fp)])+fp.encode("utf-8")
        tmp = btp+bfp
        if len(it)>2:
            _bs = it[2]
            bbs = struct.pack(">I", len(_bs))+_bs
            tmp+=bbs
        bs+=tmp
    return bs
def bts2rst(bs):
    bn = bs[:2]
    bs = bs[2:]
    n = struct.unpack(">H", bn)[0]
    rst = []
    for i in range(n):
        btp = bs[:1]
        tp = tps[itps[btp]]
        lfp = bs[1:2][0]
        fp = bs[2:2+lfp].decode("utf-8")
        bs = bs[2+lfp:]
        it = [tp, fp]
        if tp in 'ne,add'.split(","):
            l_bs = struct.unpack(">I", bs[:4])[0]
            _bs = bs[4:4+l_bs]
            bs = bs[4+l_bs:]
            it.append(_bs)
        rst.append(it)
    return rst

def fdiffs(dp1, dp2, fp):
    rst = diffs(dp1, dp2)
    bs = rst2bts(rst)
    fz.write(bs, fp)
def fupds(dp1, fp, dp2):
    bs = fz.read(fp)
    rst = bts2rst(bs)
    upds(dp1, rst, dp2)
def upd(fp1, bs_step, fp2):
    bs1 = fz.read(fp1).decode("utf-8")
    stps = tz.m_decode(bs_step)
    bs2 = tz.m_update(bs1, stps,split=0).encode("utf-8")
    fz.write(bs2, fp2)
def frp(fp):
    return fp.replace("\\","/")
def upds(dp1, rst, dp2):
    for item in rst:
        tp,fp=item[:2]
        if len(item)>2:
            bs = item[2]
        if tp == 'del':
            fz.removes(join(dp2, fp))
        elif tp == 'add':
            fz.makefdir(join(dp2, fp))
            fz.write(bs, join(dp2, fp))
        elif tp=='ne':
            fz.makefdir(join(dp2, fp))
            upd(join(dp1, fp), bs, join(dp2, fp))

pass
fetch = argx.Fetch(*xf.loads("[order, src, tgt, fp],{o:order,s:src,t:tgt,f:fp}"))

def test():
    conf = fetch()
    order,src,tgt,fp = dz.g(conf, order=0,src=0,tgt=0,fp=0)
    if order == 'diff':
        print("do diff")
        fdiffs(src, tgt, fp)
    elif order == 'recover':
        print("do recover")
        fupds(src, fp, tgt)
    print("done")

pyz.lc(locals(), test)