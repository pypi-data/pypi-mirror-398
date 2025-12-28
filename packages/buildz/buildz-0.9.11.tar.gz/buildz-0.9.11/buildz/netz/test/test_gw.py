

from buildz import xf,fz,pathz,logz,pyz
from buildz.netz import mhttp
import threading
confs = r"""
[
    {match=^/baidu, replace='www.baidu.com',ssl=true}
]
"""
rules = xf.loads(confs)
path = pathz.Path()
path.set("res", "./res")
log = logz.simple(path.res("gw/%Y%m%d.log"))
def gw():
    import sys,time
    ip = '127.0.0.1'
    port = 9999
    args = sys.argv[1:]
    if len(args)>0:
        ip = args.pop(0)
    if len(args)>0:
        port = int(args.pop(0))
    px = mhttp.Gateway((ip, port), rules, record=mhttp.MsgLog(log))
    th = threading.Thread(target=px,daemon=True)
    th.start()
    print(f"start on {(ip, port)}")
    while px.running:
        time.sleep(1)

#pyz.lc(locals(), caps)
pyz.lc(locals(), gw)

'''
cli:
import requests as rq
url="http://127.0.0.1:9999/baidu"
rp = rq.get(url)
print(rp)

'''
