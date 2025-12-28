#coding=utf-8

from . import dirz

import re
class ListsDeal(dirz.FileDeal):
    def result(self):
        return self.fps, self.errors
    def init(self):
        super().init()
        self.fps = []
        self.errors = []
    def visit(self, finfo, depth):
        fp, isdir = finfo.path, finfo.isdir
        self.fps.append([fp, isdir])
        return True
    def catch(self, finfo, depth, exp):
        fp, isdir = finfo.path, finfo.isdir
        self.errors.append([fp, isdir, exp])

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
g_codes = ["utf-8", "gbk"]
class SearchDeal(dirz.FileDeal):
    def init(self, pt_fp=None, pt = None, pt_dp = None, depth = None, relative = False, show_ct = False, shows = [10,10]):
        super().init()
        self.pt_fp = pt_fp
        self.pt_dp = pt_dp
        #if type(pt) == str:
        #    pt = pt.encode()
        if pt is not None:
            pfx = f"([\s\S]{{0,{shows[0]}}}"
            sfx = f"[\s\S]{{0,{shows[1]}}})"
            if type(pt)==bytes:
                pfx = pfx.encode()
                sfx = sfx.encode()
            pt = pfx+pt+sfx
        global g_codes
        if pt is not None:
            if type(pt) == str:
                pts = [pt.encode(c) for c in g_codes]
            else:
                pts = [pt]
        else:
            pts = None
        self.pts = pts
        self.pt = pt
        self.rst = []
        self.errs = []
        self.depth = depth
        self.relative = relative
        self.show_ct = show_ct
        self.show_list = []
    def fps(self, keep_dir = False, relative = None, fp_only = True):
        if self.show_ct:
            return self.show_list
        if relative is None:
            relative = self.relative
        rst = self.rst
        if relative:
            rst = [[i.rpath, i.isdir] for i in rst]
        else:
            rst = [[i.path, i.isdir] for i in rst]
        if not keep_dir:
            rst = [k for k in rst if not k[1]]
        if fp_only:
            rst = [k[0] for k in rst]
        return rst
    def result(self):
        if self.show_ct:
            return self.show_list
        return self.rst
    def visit(self, finfo, depth):
        if self.depth is not None and depth > self.depth:
            return False
        filepath = finfo.path
        isdir = finfo.isdir
        if self.relative:
            filepath = finfo.rpath
        if isdir:
            if finfo.empty_dir or depth==self.depth:
                if self.pt_dp is not None and len(re.findall(self.pt_dp, filepath))==0:
                    return True
                self.rst.append(finfo)
            return True
        if self.pt_fp is not None and len(re.findall(self.pt_fp, filepath))==0:
            return False
        if self.pt is not None:
            try:
                with open(filepath, 'rb') as f:
                    s = f.read()
            except Exception as exp:
                self.catch(finfo, depth, exp)
                return False
            pt = self.pt
            mark = False
            finds = None
            mark = -1
            for i in range(len(self.pts)):
                pt = self.pts[i]
                finds = re.findall(pt, s)
                if len(finds)>0:
                    mark = i
                    break
            if mark<0:
                return False
            if self.show_ct:
                arr = []
                code = g_codes[mark]
                bld = b"* "*32
                blda = b"- "*32
                bldi = b".."*32
                arr.append(bld)
                arr.append(f"filepath: {filepath}, find {len(finds)}:".encode("utf-8"))
                arr.append(bldi)
                if type(self.pt)==bytes:
                    pass
                else:
                    try:
                        s = s.decode(code)
                        pt = self.pts[mark]#.decode(code)
                        if type(pt)==bytes:
                            pt = pt.decode(code)
                        finds = re.findall(pt, s)
                    except Exception as exp:
                        print(f"error in decode {filepath}, {self.pts[mark]} with '{code}': {exp}")
                for bs_find in finds:
                    if type(bs_find)==[list, tuple]:
                        bs_find = bs_find[0]
                    if type(self.pt)==str:
                        if type(bs_find)==bytes:
                            bs_find = bs_find.decode(code)
                    #bs_find = b">>>>>>>\n"+bs_find+b"\n<<<<<<\n"
                    #bs_find += b"\n"+bld+b"\n"
                    arr.append(bs_find)
                    arr.append(bldi)
                arr.append(blda)
                arr.append(b"")
                arr =[k if type(k)==bytes else k.encode(code) for k in arr]
                arr = b"\n".join(arr)
                try:
                    arr = decode(arr)
                except Exception as exp:
                    arr = filepath
                self.show_list.append(arr)
        self.rst.append(finfo)
        return False
    def catch(self, finfo, depth, exp):
        filepath = finfo.path
        if self.relative:
            filepath = finfo.rpath
        print(f"exp in {finfo}: {exp}")
        self.errs.append([finfo, exp])
        pass

pass

def lists(fp):
    return ListsDeal().dirs(fp)

pass
def _search(dp, pt_fp = None, pt = None, pt_dp = None, depth=None, relative = False, show = False, shows = [10,10]):
    deal = SearchDeal(pt_fp, pt, pt_dp, depth,relative, show, shows)
    return deal.dirs(dp)

pass
def searchs(dp, pt_fp = None, pt = None, pt_dp = None, depth=None, relative = False, show = False, shows = [10,10]):
    deal = SearchDeal(pt_fp, pt, pt_dp, depth,relative, show, shows)
    deal.dirs(dp)
    return deal.fps(keep_dir=True, fp_only=False)

pass
def searchd(dp, pt_fp = None, pt = None, pt_dp = None, depth=None, relative = False, show = False, shows = [10,10]):
    deal = SearchDeal(pt_fp, pt, pt_dp, depth,relative, show, shows)
    deal.dirs(dp)
    return deal.fps(keep_dir=True, fp_only=True)

pass

def search(dp, pt_fp = None, pt = None, depth=None, relative = False, show = False, shows = [10,10]):
    deal = SearchDeal(pt_fp, pt, None, depth,relative, show, shows)
    deal.dirs(dp)
    return deal.fps(keep_dir=False, fp_only=True)

pass