#python
"""
测试代码
测试xf.loads和json.loads的速度
在修改json的scanner.py(不让它用c_make_scanner这个底层优化函数)
耗时对比如下：

json
time cost in <function loads at 0x0000015DEDD0D9E0>: 0.04396796226501465

xf
time cost in <function loads at 0x0000015DEDD0F100>: 0.3307473659515381

慢7倍多，感觉还能接受，之前没注意速度，更早的版本(buildz.xf.read.loads，后面可能会删掉)耗时要三四秒，对比之后就重新写了个，也不管什么堆栈了，就递归调用，后面有时间再改回堆栈吧（python的list的append和pop效率貌似不咋地，尤其是pop(0)）
又写了个C版本的代码来加速，速度大概比C加速版json的慢三到四倍（汗，和没用C加速版的json差不多速度，追求结构化不追求速度，逻辑上本来就多了不少内存分配和运算，用C只是因为C本身比python快，起码满足自己使用了，本测试代码里C加速版xf比python版快7倍，在其他场景里实际使用快了十倍以上，不过也比C版json慢了六七倍），源码暂不公布（C语言要自己写垃圾回收真累，还只是写了个计数器的，还要自己写List和Map，另外就是用C写了后，发现除了当库给其他语言使用，貌似没啥用，还有cython调用C真方便，后续可能会优化下，配置文件格式错误把错误位置打印出来，这个实现起来简单，不过不一定写，不是必要的，还有C版本的垃圾回收在抛错的时候清理下数据，不清理的话，配置文件格式错误会导致之前分配的内存未释放，内存占用增多，因为不打算直接在C用xf，打算抛错的时候，C用的内存全释放算了，之后调用再重新分配）
还有个比较操蛋的点是，用java也写了一版读取xf格式配置文件，结果java版比C版还快，一脸问号，是在C写的内存分配和回收占用时间了吗？更无语的是，java做循环读取配置文件，貌似会触发java的优化，平均速度还会更快（循环100次后和C加速版python的json差不多一样快了），不清楚是因为循环读的是一样的字符串导致的java优化，还是其他原因导致的java优化，如果是其他原因，说明读多个配置文件的时候java版会越来越快，java版会比C版更适合使用，而且java自己有垃圾回收，有List和Map，有时间下个python库用python调java试试
用C++也写了一版，用O3优化的情况下（windows里用mingw-x64的gcc/g++编译的），耗时是C版json的3倍多一点，C版O3优化的情况下是C版json的5倍左右，另外在wsl2测试了下，wsl2下更快一些，wsl2下C++版大概是C版json的2倍多一点，估计是windows下mingw-x64编译有些损耗
"""
from buildz.xf import readz as rz
try:
    from buildz.xf import readz_nexp as rz_nexp
except:
    rz_nexp=rz
from buildz.xf import read as rd
from buildz import xf, fz
import json
import time,sys

try:
    # C加速代码
    import cxf
except:
    from buildz.xf import readz as cxf
    pass
pass
def cost(n, f,*a,**b):
    c = time.time()
    r = f(*a,**b)
    d = time.time()-c
    print(f"time cost in {n}-{f}: {d}")
    return r, d

pass

n = 100
m = 13
l = 12
_arr = [123]
print("test A")
for i in range(n):
    _arr = [list(_arr)]

pass
print("test B")
_map = {}
for i in range(m):
    _map[i] = dict(_map)

pass
print("test C")
rst = []
for i in range(l):
    rst.append([_arr,_map])

pass
print("test D")
json.dumps(_arr)
print("test E")
json.dumps(_map)
print("test F")
js = json.dumps(rst)
#js = fz.read(fp, 'r')
#js = "\n\n"+js+"\n"
#js = xf.dumps(rst, json_format=1)
# js = r"""
# [
#     1,2,3,{"4":5,"6":7,"8":9,"10":11,"4":6}
# ]
# """
print("start")
num = 3
cs = [0,0,0,0]
for i in range(num):
    jv,cj = cost("json.loads", json.loads,js)
    xvbk,cxbk = cost("rz_nexp.loads", rz_nexp.loads, js)
    xv,cx = cost("rz.loads",rz.loads,js)
    cv,cv = cost("cxf.loads", cxf.loads, js)
    cs[0]+=cj
    cs[1]+=cx
    cs[2]+=cxbk
    cs[3]+=cv
print(f"judge: {jv==xv}")
print(f"judge: {jv==xvbk}")
print(f"judge: {jv==cv}")
print(f"json mean cost: {cs[0]/num}")
print(f"xf mean cost: {cs[1]/num}")
print(f"xf_nexp mean cost: {cs[2]/num}")
print(f"cxf mean cost: {cs[3]/num}")
print(f"xf cost =  {'%.3f'%(cs[1]/cs[0],)} json")
print(f"xf_nexp cost =  {'%.3f'%(cs[2]/cs[0],)} json")
print(f"cxf cost = {'%.3f'%(cs[3]/cs[0],)} json")
print(f"xf cost = {'%.3f'%(cs[1]/cs[3],)} cxf")
print(f"xf cost = {'%.3f'%(cs[1]/cs[2],)} xf_nexp")
#_xv = cost("rd.loads",rd.loads, js)
#with open("test.json", 'w') as f:
#    f.write(js)
if n>3 or m>3 or l > 3:
    exit()
print(json.dumps(jv))
print(json.dumps(xv))



