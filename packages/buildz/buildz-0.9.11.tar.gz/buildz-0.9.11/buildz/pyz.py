
import sys
import os
import hashlib
import inspect
#from .base import Base, WBase
class With:
    def __init__(self, fc_in, fc_out, args = False):
        self.fc_in = fc_in
        self.fc_out = fc_out
        self.args = args
    def __enter__(self):
        if self.fc_in is not None:
            self.fc_in()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        rst = False
        if self.fc_out is not None:
            if self.args:
                rst = self.fc_out(exc_type, exc_val, exc_tb)
            else:
                rst = self.fc_out()
        return rst

pass
def with_out(fc, args = False):
    return With(None, fc, args)

pass
def hashcode(s):
    if type(s)==str:
        s = s.encode("utf-8")
    return hashlib.md5(s).hexdigest()

pass
def add_prevdir(fp, up = 1, adds = []):
    """
        将当前文件所在目录的上{up}层目录加入sys.path，这样可以在同层写测试代码，但是写import的时候还是要当作是在上{up}层做import
    """
    if type(adds) not in [list, tuple]:
        adds = [adds]
    fp = os.path.abspath(fp)
    if os.path.isfile(fp):
        dp = os.path.dirname(fp)
    else:
        dp = fp
    for i in range(up):
        dp = os.path.dirname(dp)
    dp = os.path.join(dp, *adds)
    sys.path.insert(0, dp)

pass
add_prev_dir = add_prevdir
test_current = add_prevdir
add_path = test_current
add_current = test_current
add = test_current
def load(md, fc = None):
    """
        import object(whether module or others) from md(or md.fc)
        exp:
            load("buildz.xf") = package xf
            load("buildz.xf", "loads") = function loads from package buildz.xf
            load("buildz.xf.loads") = function loads from package buildz.xf
    """
    mds = md.split(".")
    arr = mds[1:]
    tr_exp = ''
    while len(mds)>0:
        try:
            md = __import__(".".join(mds))
            break
        except ModuleNotFoundError as exp:
            import traceback
            tr_exp = traceback.format_exc()
            mds = mds[:-1]
    if len(mds)==0:
        raise Exception("can't import package from "+md+":"+tr_exp)
    try:
        for k in arr:
            md = getattr(md, k)
        if fc is not None:
            fc = getattr(md, fc)
        else:
            fc = md
    except Exception as exp:
        raise Exception(f"get exp: {exp}, traceback: {tr_exp}")
    return fc

pass
def pyexe():
    return sys.executable

pass
exe=pyexe
is_windows = sys.platform.lower()=='win32'
def pypkg():
    """
        return python package path, test on linux and windows
    """
    try:
        import buildz
        import os
        return os.path.dirname(buildz.__path__[0])
    except:
        pass
    import site
    sites = site.getsitepackages()
    if is_windows:
        fpath = sites[-1]
    else:
        fpath = sites[0]
    return fpath

pass
pkg = pypkg
pth = pypkg

class Pth:
    def __init__(self, fp = "build.pth"):
        self.fp = os.path.join(pth(), fp)
    def read(self):
        fp = self.fp
        if not os.path.isfile(fp):
            return []
        with open(fp, 'rb') as f:
            s = f.read().decode()
        return s.split("\n")
    def add(self, path):
        arr = self.read()
        if path in arr:
            print("alread add")
            return
        arr.append(path)
        self.write(arr)
    def write(self, paths = []):
        if type(paths) not in [list, tuple]:
            paths = [paths]
        s = "\n".join(paths)
        with open(self.fp, 'wb') as f:
            f.write(s.encode())
    def remove(self):
        os.remove(self.fp)

pass

_pth = Pth()
def main(name, fc, *args, **maps):
    if name=="__main__":
        fc(*args, **maps)

pass

def bylocals(mlocals, fc, *args, **maps):
    if mlocals['__name__']=="__main__":
        fc(*args, **maps)

pass
#lcmain=bylocals
lc_main=bylocals
lc = bylocals
local = bylocals
def mainerr(fc, *args, **maps):
    st = inspect.stack()[1]
    if st.filename == '<stdin>':
        fc(*args, **maps)
    else:
        print("not main:", st.filename)

pass

def not_null(*args, exp_def=None):
    for v in args:
        if v is not None:
            return v
    return ret_exp_def(exp_def)
nnull = not_null
class exp_def_enp:
    def __init__(self, exp=False, default=None, exp_fc = Exception, exp_args = [], exp_maps = {}):
        self.exp_fc = exp_fc
        self.exp_args = exp_args
        self.exp_maps=exp_maps
        self.exp = exp
        self.default = default
    def __call__(self, exp=None, default=None, exp_fc = None, exp_args=None, exp_maps=None):
        exp = not_null(exp, self.exp)
        default = not_null(default, self.default)
        exp_fc = not_null(exp_fc, self.exp_fc)
        exp_args=not_null(exp_args, self.exp_args)
        exp_maps = not_null(exp_maps, self.exp_maps)
        if exp:
            raise exp_fc(*exp_args, **exp_maps)
        return default
pass
def default(val):
    return exp_def_enp(False, val)

exp_def = exp_def_enp
def ret_exp_def(val):
    if isinstance(val, exp_def_enp):
        return val()
    return val

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
def encode(bs, coding="utf-8"):
    coding = coding.lower()
    xcoding = 'utf-8'
    if coding == 'utf-8':
        xcoding = 'gbk'
    try:
        return bs.encode(coding)
    except:
        return bs.encode(xcoding)


def fc_input(s, fc_done):
    s = input(s)
    fc_done(s)

pass
def th_input(s, fc_done):
    import threading as th
    t = th.Thread(target=fc_input, args=(s, fc_done), daemon=True)
    t.start()

pass