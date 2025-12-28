
import socket, select, traceback, threading, time
from buildz import Base, logz, pyz

log = logz.simple()
class MiddleServer(Base):
    '''
        端口映射
        简单调用:
            python -m buildz.netz.tcp 监听ip 监听端口 目标ip 目标端口
    '''
    def init(self, addr, remote_addr, listen=5,wait=0.1, read_size=1024*1024):
        self.addr = tuple(addr)
        self.listen = listen
        self.remote_addr = tuple(remote_addr)
        self.read_size = read_size
        self.running = False
        self.wait = wait
        self.pairs = {}
        #self.lock = threading.Lock()
    def close_pair(self, a, b):
        #with self.lock:
        del self.pairs[id(a)]
        del self.pairs[id(b)]
        log("close").info(f"pair {a.getpeername()}, {b.getpeername()} close")
        for c in (a,b):
            try:
                c.close()
            except:
                pass
    def deal(self, skt):
        skt_read, skt_write = self.pairs[id(skt)]
        try:
            bts = skt_read.recv(self.read_size)
            if len(bts)==0:
                self.close_pair(skt_read, skt_write)
                return
            skt_write.send(bts)
            log("send").info(f"{skt_read.getpeername()} to {skt_write.getpeername()}: {len(bts)} bytes")
        except Exception as exp:
            log.debug(f"deal exp: {exp}")
            log.warn(f"traceback: {traceback.format_exc()}")
            self.close_pair(skt_read, skt_write)
    def connects(self):
        #with self.lock:
        arr = [v[0] for k,v in self.pairs.items()]
        return arr
    def add(self, skt_cli, addr):
        try:
            skt_srv = socket.socket()
            skt_srv.connect(tuple(self.remote_addr))
        except Exception as exp:
            log.error(f"add exp: {exp}")
            log.error(f"traceback: {traceback.format_exc()}")
            skt_cli.close()
            return
        log("connect").info(f"build pair from {skt_cli.getpeername()} to {skt_srv.getpeername()}")
        #with self.lock:
        self.pairs[id(skt_cli)] = (skt_cli, skt_srv)
        self.pairs[id(skt_srv)] = (skt_srv, skt_cli)
    def call(self, fc_stop = None):
        self.running=True
        if fc_stop is None:
            return self.waits_and_deals()
        else:
            threading.Thread(target=self.waits_and_deals,daemon=True).start()
            try:
                while not fc_stop():
                    time.sleep(1.0)
            finally:
                self.running=False
    def waits_and_deals(self):
        skt = socket.socket()
        skt.bind(self.addr)
        skt.listen(self.listen)
        self.skt = skt
        while self.running:
            skts = self.connects()
            skts.append(self.skt)
            (rlist,wlist,elist)=select.select(skts,[],[],self.wait)
            for skt in rlist:
                if skt == self.skt:
                    _skt,addr = self.skt.accept()
                    self.add(_skt, addr)
                else:
                    self.deal(skt)
    def waits(self):
        skt = socket.socket()
        skt.bind(self.addr)
        skt.listen(self.listen)
        self.skt = skt
        while self.running:
            skt,addr = self.skt.accept()
            self.add(skt, addr)
    def deals(self):
        while self.running:
            if len(self.pairs)==0:
                time.sleep(self.wait)
                continue
            (rlist,wlist,elist)=select.select(self.connects(),[],[],0)
            for skt in rlist:
                self.deal(skt)

pass

def test():
    import sys
    args = sys.argv[1:]
    ip = args.pop(0)
    port = int(args.pop(0))
    addr = (ip, port)
    ip = args.pop(0)
    port = int(args.pop(0))
    remote_addr = (ip, port)
    MiddleServer(addr, remote_addr)()

pass
