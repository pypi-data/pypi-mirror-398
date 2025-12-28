

from buildz import xf,fz,pathz,logz
from buildz.netz import mhttp
import threading
try:
    from buildz.netz import sslz
except:
    print(f"need package cryptography: pip install cryptography")
    raise

path = pathz.Path()
path.set("res", "./res")
fp_prv = path.res("ca.prv")
fp_cert = path.res("ca.crt")
ca_pwd = "test"


ca_conf = xf.loads(r"""
// 国家
country: CN
// 省份
provice: fujian
// 城镇
local: quanzhou
// 机构
org: buildz
// 域名
comman: buildz
// 邮箱
email: netz@buildz
// 是否是ca
ca: true
//dns: [localhost]
// 签名有效提前时间（签名多少天前就有效）
valid_before: 1
// 签名有效时间（签名后有效多少天）
valid: 3650
ca:true
""")
log = logz.simple(path.res("caps/%Y%m%d.log"))
fz.makedir(path.res())
def gen_cert():
    import os
    if os.path.isfile(fp_cert) and os.path.isfile(fp_prv):
        return
    sslz.gen_prv(fp_prv, ca_pwd)
    sslz.gen_cert(fp_cert,fp_prv, ca_conf, ca_pwd)


def caps():
    gen_cert()
    import sys,time
    ip = '127.0.0.1'
    port = 9999
    args = sys.argv[1:]
    if len(args)>0:
        ip = args.pop(0)
    if len(args)>0:
        port = int(args.pop(0))
    px = mhttp.CapsProxy((ip, port), fp_cert, fp_prv, ca_pwd, record=mhttp.MsgLog(log))
    th = threading.Thread(target=px,daemon=True)
    th.start()
    print(f"start on {(ip, port)}")
    while px.running:
        time.sleep(1)

#pyz.lc(locals(), caps)


