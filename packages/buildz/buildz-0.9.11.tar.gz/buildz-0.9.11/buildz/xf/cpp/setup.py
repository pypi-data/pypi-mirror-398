#coding=utf-8
import sys
import os
curr_dir = os.path.dirname(__file__)
mark_msvc = False
mark_mingw32 = False
if len(sys.argv)==1:
    sys.argv.append("build_ext")
    #sys.argv.append("--inplace")
    sys.argv.append('--build-lib')
    sys.argv.append(f"{curr_dir}")
if sys.platform=='win32':
    mark_msvc = True
    for k in sys.argv[1:]:
        if k.find("--compiler=")==0:
            v=k[len("--compiler="):].strip().lower()
            mark_msvc = v=='msvc'
            mark_mingw32 = v=='mingw32'
            break
from distutils.core import setup, Extension
from Cython.Build import cythonize
extra_link_args = []
define_macros=[]
extra_compile_args = []
sources = [os.path.join(curr_dir, "pcxf.pyx"),os.path.join(curr_dir, "pc.cpp")]
from buildz import fz
cpps = fz.search(os.path.join(curr_dir,"loaderz"),".*\.cpp")
sources+=cpps
if not mark_msvc:
    extra_link_args = ["-lstdc++", "-O3"]
    extra_compile_args = ["-O3"]
else:
    extra_compile_args = ["/O2"]
if mark_mingw32:
    define_macros = [("MS_WIN64",1)]
    from setuptools._distutils import cygwinccompiler
    msvcrs = cygwinccompiler.get_msvcr()
    if "ucrt" in msvcrs:
        # windows下没有预装ucrt，但python编译要ucrt，直接把mingw相关的库静态打包进去，就不用ucrt了
        cygwinccompiler.get_msvcr = lambda :[]
        extra_link_args.append("-static")
#extra_link_args.append("-static")

setup(
    ext_modules = cythonize(Extension(
        "pcxf",
        language="c++",
        sources = sources,
        include_dirs=[os.path.join(curr_dir,"loaderz"),curr_dir],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,  # 链接 C++ 标准库
        define_macros=define_macros,
    )),
)
