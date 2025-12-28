#coding=utf-8
import os
"""
读写文件再简化
"""
def fread(fp, mode='rb'):
    with open(fp, mode) as f:
        return f.read()

pass
read=fread
def freads(fp, mode = 'rb', size=1024*1024):
    with open(fp, mode) as f:
        while True:
            bs = f.read(size)
            if len(bs)==0:
                break
            yield bs

pass
reads=freads

def fwrite(ct, fp, mode = 'wb'):
    with open(fp, mode) as f:
        f.write(ct)

pass
write = fwrite
def fwrites(cts, fp, mode = 'wb'):
    with open(fp, mode) as f:
        for ct in cts:
            f.write(ct)

pass
writes = fwrites

def makedir(dp):
    if os.path.isdir(dp):
        return
    os.makedirs(dp)

pass
def makefdir(fp):
    fp = os.path.abspath(fp)
    dp = os.path.dirname(fp)
    makedir(dp)

pass

def dirpath(fp, n=1):
    for i in range(n):
        fp = os.path.dirname(fp)
    return fp

pass

dirname = dirpath

def coverx(sz, chars=None):
    if chars is None:
        chars = b"a"
    if type(chars)==str:
        chars = chars.encode("utf-8")
    l = sz//len(chars)
    cs = chars*l
    left = sz%len(chars)
    cs+=chars[:left]
    return cs
def fcover(filepath, wsize = 1024*10, chars=None):
    st = os.stat(filepath)
    size = st.st_size
    #print(f"{filepath}:{size}")
    #bs = b'a'*wsize
    with open(filepath, 'wb') as f:
        for i in range(0, size, wsize):
            sz = min(size-i, wsize)
            bs = coverx(sz, chars)
            #print(f"bs: {len(bs)}, sz: {sz}, i:{i}, wsize:{wsize}")
            f.write(bs)

pass
cover = fcover
def removes(fp, cover = False,wsize = 1024*10,chars=None):
    if not os.path.exists(fp):
        return
    if os.path.isfile(fp):
        #print(f"remove file '{fp}'")
        if cover:
            fcover(fp,wsize=wsize, chars=chars)
        os.remove(fp)
        return
    fps = os.listdir(fp)
    fps = [os.path.join(fp, f) for f in fps]
    [removes(f, cover) for f in fps]
    #print(f"removedirs '{fp}'")
    os.rmdir(fp)

pass
def decode(s, coding = 'utf-8'):
    coding = coding.lower()
    xcoding = 'utf-8'
    if coding == 'utf-8':
        xcoding = 'gbk'
    try:
        return s.decode(coding)
    except:
        return s.decode(xcoding)

pass

def sread(fp, code='utf-8', mode='r'):
    if mode.find("b")<0:
        mode+="b"
    return decode(read(fp, mode), code)

pass
def swrite(dt, fp, code="utf-8", mode = "w"):
    if mode.find("b")<0:
        mode+="b"
    if type(dt)!=bytes:
        dt = dt.encode(code)
    write(dt, fp, mode)

pass

def is_abs(fp):
    if fp is None:
        return False
    if fp.strip()=="":
        return False
    fp = fp.strip().replace("\\", "/")
    if fp[0]=="/":
        return True
    arr = fp.split("/")
    if arr[0].find(":")>=0:
        return True
    return False

pass
    
def xors(bs, codes):
    if type(codes)==str:
        codes = codes.encode("utf-8")
    rst = b''
    codes= list(codes)
    for i in range(0, len(bs), len(codes)):
        _bs = bs[i:i+len(codes)]
        rs = bytes([a^b for a,b in zip(_bs, codes)])
        rst+=rs
        codes = codes[1:]+codes[:1]
    return rst

def fxors(fp, codes, ofp=None):
    bs = read(fp, 'rb')
    bs = xors(bs, codes)
    if ofp is not None:
        write(bs, ofp, 'wb')
    else:
        return bs

pass
def covers(dp, chars=None,wsize = 1024*10,):
    if not os.path.exists(dp):
        return
    from . import lsf
    fs = lsf.search(dp)
    #print(f"fs: {fs}")
    for fp in fs:
        fcover(fp,wsize=wsize, chars=chars)

pass
fcovers = covers