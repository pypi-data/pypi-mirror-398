#codig=utf-8
import os
import re
import base64
ACT_ADD = "add_prev"
ACT_DEL = "del_curr"
import struct
def encode(steps, as_str = False):
    """
        步骤列表转bytes/str
    """
    rst = b""
    # 加减的长度设置最多2**15-1，保留1位当作“加/减”，4位整数当字符串位置索引
    max16 = 2**15-1
    for step in steps:
        if step[0] == ACT_ADD:
            bs = step[2]
            if type(bs) == str:
                bs = bs.encode("utf-8")
            bs_arr = []
            while len(bs)>max16:
                cut = bs[:max16]
                bs = bs[max16:]
                bs_arr.append(cut)
            if len(bs)>0:
                bs_arr.append(bs)
            for bs in bs_arr:
                obj = struct.pack(">HI", len(bs)*2+1, step[1])+bs
                rst+=obj
        else:
            s1 = step[1]
            s2 = step[2]
            nexts = [s1]
            while (s2-s1)>max16:
                nexts.append(s1+max16)
                s1+=max16+1
            if s1<=s2:
                nexts.append(s2)
            for i in range(1,len(nexts)):
                obj = struct.pack(">HI", (nexts[i]-nexts[i-1])*2, nexts[i-1])
                rst+=obj
        #rst+=obj
    if as_str:
        rst = base64.b64encode(rst).decode()
    return rst

pass
def decode(obj):
    """
        bytes/str转步骤列表
    """
    if type(obj) == str:
        obj = base64.b64decode(obj)
    ni = 2+4
    rst = []
    while len(obj)>0:
        bs = obj[:ni]
        obj = obj[ni:]
        v2, base = struct.unpack(">HI", bs)
        act = v2%2
        c = v2//2
        #act, base, c = struct.unpack(">HI", bs)
        if act == 1:
            bs = obj[:c]
            obj = obj[c:]
            s = bs.decode("utf-8")
            tmp = [ACT_ADD, base, s]
        else:
            tmp = [ACT_DEL, base, base+c]
        rst.append(tmp)
    return rst

pass
def steps(vs, n, m, d, stra, strb):
    k = n-m
    rst = []
    for step in range(d, 0, -1):
        v = vs[step]
        x = v[k]
        y = x-k
        prev_v = vs[step-1]
        down = ((k == -step) or ((k != step) and prev_v[k + 1] > prev_v[k - 1]))
        prev_k = k+1 if down else k-1
        prev_x = prev_v[prev_k]
        prev_y = prev_x-prev_k
        if down:
            #加字符
            act = [ACT_ADD, prev_x, strb[prev_y]]
        else:
            #删字符
            act = [ACT_DEL, prev_x, prev_x, stra[prev_x]]
        rst.append(act)
        k = prev_k
    rst.reverse()
    rst = combine(rst)
    return rst

pass
def combine(steps):
    base = None
    rst = []
    for step in steps:
        if len(rst)>0 and rst[-1][0] == step[0]:
            prev = rst[-1]
            if step[0] == ACT_ADD:
                if prev[1]==step[1]:
                    prev[2]+=step[2]
                    continue
            elif step[0] == ACT_DEL:
                if prev[2] == step[1]-1:
                    prev[2] = step[2]
                    continue
            else:
                raise Exception("test")
        rst.append(step)
    return rst

pass
def count(steps):
    cnt = 0
    cadd,cdel = 0,0
    #print(f"steps: {len(steps)}")
    for step in steps:
        if step[0] == ACT_ADD:
            cnt+=len(step[2])
            cadd+=len(step[2])
        else:
            cnt+=1+step[2]-step[1]
            cdel +=1+step[2]-step[1]
    return cnt#,cadd,cdel

pass
def update(s, steps, split=1):
    """
        按照steps更新s
    """
    if split:
        if type(s)!=list:
            s = spt(s)
    if type(s)==bytes:
        s = [s[i:i+1] for i in range(len(s))]
    updated = -1
    rst = []
    spc = ""
    if type(s)==bytes or type(s[0])==bytes:
        spc = b""
    for step in steps:
        act = step[0]
        x = step[1]
        c = step[2]
        if updated+1<x:
            tmp = s[updated+1:x]
            rst.append(tmp)
        if act == ACT_ADD:
            rst.append(c)
            updated = x-1
        elif act == ACT_DEL:
            updated = c
        else:
            raise Exception("test")
    if updated+1 < len(s):
        rst.append(s[updated+1:])
    rst = [k if type(k)!=list else spc.join(k) for k in rst]
    rs = spc.join(rst)
    return rs

pass
def spt(s, spts = "\n'\" `~!@#$%^&*()_+-={}[]:;<>,.?/|"):
    arr = [s]
    spts = list(spts)
    if type(s)==bytes:
        spts = [k.encode() for k in spts]
    for _spt in spts:
        tmp = []
        for s in arr:
            s = s.split(_spt)
            # r = []
            # for k in s:
            #     r.append(k)
            #     r.append(_spt)
            # s = r[:-1]
            s = [k+_spt for k in s[:-1]]+[s[-1]]
            tmp+=s
        arr = tmp
    return arr

pass
def myers(stra, strb, split = 1):
    import time
    curr = time.time()
    if split:
        if type(stra)!=list:
            stra = spt(stra)
        if type(strb)!=list:
            strb = spt(strb)
    if type(stra)==bytes:
        stra = [stra[i:i+1] for i in range(len(stra))]
    if type(stra)==bytes:
        strb = [strb[i:i+1] for i in range(len(strb))]
    n = len(stra)
    m = len(strb)
    v = {
        1:0
    }
    vs = {
        0: {1:0}
    }
    index = 0
    total=0
    for d in range(n+m+1):
        tmp = {}
        for k in range(-d, d+1, 2):
            # k == -d, 左边界，没法从左边来，只能是上边往下，k==d,上边界，只能从左边过来，
            # v[k-1]是上一轮迭代，k-1线上的步数，从上一步的k-1到这一步的k，是向右，删字符，
            # 因为上一步算了k从-d+1到d-1，所以除了边界可能没有左右值，中间的k都能查到上一步的k+1和k-1
            # v[k+1]>v[k-1]，表示向下（加字符）的x比向右（删字符）的x大
            # 可以看图，k+1和k-1是k旁边的两条线，如果v[k+1]<=v[k-1]，说明k-1的点在k+1的下方或右边，看图会发现k-1这个点更接近k这条线的终点
            down = ((k == -d) or ((k != d) and v[k + 1] > v[k - 1]))
            kPrev = k+1 if down else k-1
            xStart = v[kPrev]
            yStart = xStart - kPrev
            # 完全没啥用的两个中间变量。。。
            xMid = xStart if down else xStart + 1
            yMid = xMid - k
            xEnd = xMid
            yEnd = yMid
            while xEnd < n and yEnd < m and stra[xEnd] == strb[yEnd]:
                xEnd+=1
                yEnd+=1
                total+=1
            v[k] = xEnd
            tmp[k] = xEnd
            index+=1
            total+=1
            if xEnd == n and yEnd == m:
              vs[d] = tmp
              sec = time.time()-curr
              stps = steps(vs, n,m,d,stra, strb)
              return stps
        vs[d] = tmp

pass

"""

python -m buildz myers


python -m buildz myers diff "D:\rootz\python\gits\buildz_upd\buildz\tz\myers_diff.py" "D:\rootz\python\wk\test\myers_diff.py" "D:\rootz\python\wk\test\stp.txt" +e


python -m buildz myers update "D:\rootz\python\gits\buildz_upd\buildz\tz\myers_diff.py" "D:\rootz\python\wk\test\myers_diff_.py" "D:\rootz\python\wk\test\stp.txt" +e

python -m buildz myers diff "D:\rootz\python\wk\test\myers_diff.py" "D:\rootz\python\wk\test\myers_diff_.py" "D:\rootz\python\wk\test\df.txt" +t

"""