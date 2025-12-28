#coding=utf-8
import os
class FileInfo:
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return f"<path='{self.path}', rpath='{self.rpath}' isdir={self.isdir}>"
    def __init__(self, path, rpath, base_dir, isdir, empty_dir=False, visit_dir = False):
        self.path = path
        self.rpath = rpath
        self.base_dir = base_dir
        self.isdir = isdir
        self.empty_dir = empty_dir
        self.visit_dir = visit_dir
        self.name = os.path.basename(path)
        self.dirpath = os.path.dirname(path)
        self.rdirpath = os.path.dirname(rpath)

pass
#列出文件夹下所有文件和文件更新时间
#文件访问处理方法
#建议visit读取文件
#catch处理目录访问异常
class FileDeal:
    def __init__(self, *argv, **maps):
        self.init(*argv, **maps)
    def result(self):
        return None
    def reset(self, filepath, depth=0):
        pass
    def init(self, *argv, **maps):
        pass
    def work(self, *argv, **maps):
        return self.dirs(*argv, **maps)
    def dirs(self, filepath, depth = 0):
        self.reset(filepath, depth)
        dirs(filepath, self, depth)
        return self.result()
    def visit(self, fileinfo, depth):
        return True
    def catch(self, filepinfo, depth, exp):
        pass
    def deal(self, filepinfo, depth, exp = None):
        if exp is None:
            return self.visit(filepinfo, depth)
        else:
            return self.catch(filepinfo, depth, exp)
    def __call__(self, *argv, **maps):
        return self.deal(*argv, **maps)

pass
#遍历文件／文件夹filepath
def dirs(filepath, fc=FileDeal(), depth = 0, base_dir = None, rpath = None):
    if base_dir is None:
        base_dir = filepath
    if rpath is None:
        rpath = ""
    isdir = os.path.isdir(filepath)
    finfo = FileInfo(filepath, rpath, base_dir, isdir)
    visit = fc(finfo, depth)
    if isdir and visit:
        try:
            files = os.listdir(filepath)
        except Exception as exp:
            finfo = FileInfo(filepath, rpath, base_dir, isdir, False, True)
            fc(finfo, depth, exp)
            return
        if len(files)==0:
            finfo = FileInfo(filepath, rpath, base_dir, isdir, True, True)
            fc(finfo, depth)
        files = [
            [
                os.path.join(filepath, file),
                os.path.join(rpath, file)
            ]
            for file in files]
        [dirs(fp[0], fc, depth+1, base_dir, fp[1]) for fp in files]

pass

