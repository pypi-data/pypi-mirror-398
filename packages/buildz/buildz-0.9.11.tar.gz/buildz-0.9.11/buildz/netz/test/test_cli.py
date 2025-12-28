#
try:
    import requests as rq
except:
    print("need package requests: pip install requests")
    raise
session = rq.session()
from buildz import pathz

path = pathz.Path()
path.set("res", "./res")
fp_cert = path.res("ca.crt")
import sys
ip = "127.0.0.1"
port=9999
args = sys.argv[1:]
if len(args)>0:
    ip = args.pop(0)
if len(args)>0:
    port =int(args.pop(0))
proxies = {
    'http':f'http://{ip}:{port}',
    'https':f'http://{ip}:{port}'
}

url = "https://www.baidu.com"
verify=fp_cert
rp = session.get(url, proxies = proxies,verify=verify)
print(rp,len(rp.content))

url = "http://www.baidu.com"
rp = session.get(url, proxies = proxies,verify=verify)
print(rp,len(rp.content))

url = "https://www.bilibili.com/"
headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding":"gzip, deflate, br, zstd",
    "Accept-Language":"zh-CN,zh;q=0.9"
}
rp = session.get(url, proxies = proxies,verify=verify,headers=headers)
print(rp,len(rp.content))