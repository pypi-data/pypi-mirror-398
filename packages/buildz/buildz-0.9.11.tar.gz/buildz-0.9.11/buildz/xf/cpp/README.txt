1，简介：
用C++重写了一版xf.loads和xf.loadx，
mingw32-x64编译的C++版速度大概是python版的9倍
linux gnu编译的C++版速度大概是python版的15倍
windows下msvc没试过，因为没装
但不管怎么说，都比Python的C版json慢，linux gnu编译的C++版性能是C版json的三分之一

2，编译：

需要先安装Cython：
pip install Cython

然后进行编译：

linux下：
python setup.py

windows + mingw32-x64:
python setup_mingw32.py

windows下的msvc/vs(没试过，感觉有可能会报错，要自己改setup.py，不用msvc的原因是嫌vs太大了，不想装):
python setup.py

mac没试过，苹果电脑没用过

3，使用：
编译好之后就自动引用了，编译好之后运行的python，使用的buildz.xf.load*会自动替换成C++版
也可以手动引用：
from buildz.xf.cpp.pcxf import loads, loadx