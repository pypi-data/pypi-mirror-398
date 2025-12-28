
'''
http协议模拟
'''
import socket
import select
from buildz import Base, logz
import traceback
# log = logz.simple("./logs/mhttp/%Y%m%d.log")
# 默认日志只打印不存文件
log = logz.simple()
def http_encode(line, headers=None,data_size=0):
    if type(line)==str:
        line = line.encode("utf-8")
    if line[-2:]!=b"\r\n":
        line+=b"\r\n"
    rst = [line]
    if headers is None:
        headers = {}
    if data_size > 0:
        headers['Content-Length'] = data_size
    for key,val in headers.items():
        rst.append(f"{key}: {val}\r\n".encode("utf-8"))
    rst.append(b"\r\n")
    #if data is not None:
    #    rst.append(data)
    rs = b"".join(rst)
    return rs
pass
def http_recv(rfile):
    "out: line(str), headers(dict), raw_data(bytes or null)"
    #rfile = skt.makefile('rb', buffer_size)
    line = rfile.readline()
    if len(line)==0:
        return None,None,None
    #log.debug(f"http_recv: {line}")
    line = line.decode("utf-8")
    headers = {}
    data = None
    dt_size = 0
    while True:
        next = rfile.readline().strip()
        if len(next)==0:
            break
        index = next.find(b": ")
        key = next[:index].decode("utf-8")
        val = next[index+2:].decode("utf-8")
        if key == 'Content-Length':
            val = int(val)
            dt_size = val
        headers[key] = val
    #if dt_size>0:
    #    data = rfile.read(dt_size)
    #rfile.close() # not keep-alive
    return http_decode(line), headers, dt_size
pass
def http_decode(line):
    index = line.find(" ")
    a, line = line[:index], line[index+1:]
    index = line.find(" ")
    b, c = line[:index], line[index+1:]
    #log.debug(f"http_docde: {a,b,c}")
    return a,b,c.strip()
pass
def spt_url(url):
    index = url.find("://")
    prev = url[:index]
    url = url[index+3:]
    addr = url.split("?")[0].split("/")[0]
    url = url[len(addr):]
    if len(url)==0 or url[0]!="/":
        url = "/"+url
    return prev, addr, url

pass
def comb_url(prev, addr, url):
    return prev+"://"+addr+url
def http_encode_send(http_type, url, headers=None, data_size=0, protocol = "HTTP/1.1"):
    prev, addr, url = spt_url(url)
    addrs = addr.split(":")
    ip = addrs[0]
    if prev.upper()=="HTTP":
        port = 80
    elif prev.upper()=="HTTPS":
        port = 443
    else:
        port = 0
    if len(addrs)>1:
        port = int(addrs[1])
    quest= f"{http_type.upper()} {url} {protocol}".encode("utf-8")
    if headers is None:
        headers = {}
    if 'Host' not in headers:
        headers['Host'] = addr
    keep_alive = 'Connection' in headers and headers['Connection'] == 'keep-alive'
    #log.debug(f"http_encode_send: {quest, headers, data_size}")
    bts = http_encode(quest, headers, data_size)
    return bts, (ip, port),keep_alive
def http_encode_rsp(code, rsp_text, headers=None, data_size=0, protocol = "HTTP/1.1"):
    line = f"{protocol} {code} {rsp_text}".encode("utf-8")
    return http_encode(line, headers, data_size)
pass
def chunked_encode(data):
    n = hex(len(data))[2:].encode()
    return n+b"\r\n"+data+b"\r\n"
def readable(skt,timeout=0):
    (rlist,wlist,elist)=select.select([skt],[],[],timeout)
    return len(rlist)>0
def chunked_data(skt):
    dt = skt.readline().strip().decode()
    n = int(dt, 16)
    dt = skt.read(n+2)[:-2]
    return n, dt
def check_chunked(headers):
    chunked = 'Transfer-Encoding' in headers and headers['Transfer-Encoding']=='chunked'
    return chunked
# Base纯粹是代码简写，懒得写__XX__的形式
class WSocket(Base):
    def readable(self):
        return readable(self.skt)
    @staticmethod
    def Connect(addr, buffer_size=-1):
        skt = WSocket(buffer_size)
        skt.connect(addr)
        return skt
    @staticmethod
    def Bind(skt, buffer_size=-1, addr=None):
        wskt = WSocket(buffer_size)
        wskt.bind(skt, addr)
        return wskt
    def init(self, buffer_size=-1):
        self.buffer_size = buffer_size
        w_buffer_size = buffer_size
        if w_buffer_size<0:
            w_buffer_size=0
        self.w_buffer_size = w_buffer_size
    def bind(self, skt, addr=None):
        if addr is None:
            addr = skt.getpeername()
        self.addr = addr
        rfile = skt.makefile('rb', self.buffer_size)
        wfile = skt.makefile('wb', self.w_buffer_size)
        self.skt = skt 
        self.rfile = rfile
        self.wfile = wfile
        self.send = skt.send
        self.recv = skt.recv
        self.write = wfile.write
        self.read = rfile.read
        self.readline = rfile.readline
        self.sendall = skt.sendall
    def connect(self, addr, skt=None):
        if skt is None:
            skt = socket.socket()
            log.debug(f"connect: {addr}")
            skt.connect(tuple(addr))
        self.bind(skt, addr)
    def closefile(self):
        try:
            self.rfile.close()
            self.wfile.close()
        except:
            pass
    def close(self):
        self.closefile()
        try:
            self.skt.close()
        except:
            pass
class SendDone(Base):
    def init(self, skt, to_rel):
        self.skt = skt
        self.to_rel = to_rel
    def call(self):
        if not self.to_rel:
            return
        self.skt.close()
def http_send_head(http_type, url, headers=None, data_size=0,protocol='HTTP/1.1', skt=None, caches=None, fc_connect=None):
    if caches is None:
        caches = {}
    bts, addr,keep_alive = http_encode_send(http_type, url, headers, data_size,protocol=protocol)
    pfx = spt_url(url)[0].lower()
    if fc_connect is None:
        fc_connect = WSocket.Connect
    #log.debug(f"request addr: {addr}")
    #log.debug(f"http_send: {len(bts)}")
    retry=0
    use_caches=skt is None and keep_alive
    need_rel = keep_alive
    addr_key = tuple([pfx]+list(addr))
    if skt is None:
        if not keep_alive or addr_key not in caches:
            skt = fc_connect(addr)
        else:
            skt = caches[addr_key]
            retry=1
    else:
        need_rel=False
    fc_done = SendDone(skt, need_rel)
    try:
        skt.send(bts)
    except:
        if retry:
            skt=fc_connect(addr)
            skt.send(bts)
        else:
            raise
    if use_caches:
        caches[addr_key]=skt
    return skt,fc_done

class HttpMonitor(Base):
    """
        逻辑梳理，模拟http调用，没实际调用
    """
    def close(self):
        for addr, skt in self.skts.items():
            skt.close()
    def init(self,protocol = "HTTP/1.1"):
        self.protocol = protocol
        self.skts = {}
    def send(self, http_type, url, headers=None, data=None,protocol=None, skt=None):
        ldata = 0
        if data is not None:
            if type(data)!=bytes:
                data = str(data).encode("utf-8")
            ldata = len(data)
        else:
            data = b''
        if protocol is None:
            protocol = self.protocol
        skt, fc_done = http_send_head(http_type, url, headers, ldata, protocal,None, self.skts)
        if ldata>0:
            skt.send(data)
        return skt,fc_done
    def chunked_data(self, skt):
        return chunked_data(skt)
    def check_chunked(self, headers):
        return check_chunked(headers)
    def request(self, http_type, url, headers=None, data=None,protocol=None):
        skt,fc_done = self.send(http_type, url, headers, data,protocol)
        line, headers, data_size=http_recv(skt.rfile)
        data = b''
        if data_size>0:
            data = skt.read(data_size)
        if check_chunked(headers):
            while True:
                n, dt = self.chunked_data(skt)
                data+=dt
                if n==0:
                    break
        fc_done()
        return line, headers, data