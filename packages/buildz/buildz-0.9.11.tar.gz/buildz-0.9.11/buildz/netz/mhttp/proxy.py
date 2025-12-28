import socket,threading
from . import mhttp
from . import record as _record
from buildz import Base
import traceback
log = mhttp.log
class ProxyDealer(Base):
    """
        http和https代理
    """
    def init(self, skt, channel_read_size=1024000, record=None, protocol = "HTTP/1.1", default_deal=None):
        self.wskt = mhttp.WSocket.Bind(skt)
        self.channel_read_size = channel_read_size
        self.deals = {}
        if default_deal is None:
            default_deal = self.default_deal
        self.deals[None] = default_deal
        self.deals['CONNECT'] = self.connect_deal
        self.skts = {}
        self.protocol = protocol
        if record is None:
            record = _record.MsgLog(log)
        self.record = record
    def simple_chunked(self, skt_read, skt_send=None):
        while True:
            n, dt = mhttp.chunked_data(skt_read)
            self.record.add_chunk(dt)
            bts = mhttp.chunked_encode(dt)
            if skt_send is not None:
                skt_send.send(bts)
            if n==0:
                break
    def do_connect(self, addr):
        return mhttp.WSocket.Connect(addr)
    def default_deal(self, skt_cli, line, headers, data_size, skt=None, fc_connect=None):
        if fc_connect is None:
            fc_connect = self.do_connect
        self.record.request(line, headers, data_size)
        http_type, url, protocol = line
        skt,fc_done = mhttp.http_send_head(http_type, url, headers, data_size,protocol, skt, self.skts, fc_connect)
        if data_size>0:
            data = skt_cli.read(data_size)
            skt.send(data)
            self.record.add(data)
        if mhttp.check_chunked(headers):
            self.simple_chunked(skt_cli, skt)
        self.record.finish()
        line, headers, data_size=mhttp.http_recv(skt)
        self.record.response(line, headers, data_size)
        protocol, code, rsp_text = line
        bts = mhttp.http_encode_rsp(code, rsp_text, headers, data_size, protocol)
        skt_cli.send(bts)
        if data_size>0:
            data = skt.read(data_size)
            skt_cli.send(data)
            self.record.add(data)
        if mhttp.check_chunked(headers):
            self.simple_chunked(skt, skt_cli)
        self.record.finish()
        fc_done()
    def close(self):
        self.wskt.close()
        for addr,skt in self.skts.items():
            try:
                skt.close()
            except:
                pass
    def error(self, skt_cli, code=404, txt="Not Found", data=None):
        if data is None:
            data = txt
        if type(data)==str:
            data = data.encode("utf-8")
        bts = mhttp.http_encode_rsp(code, txt, data_size=len(data), protocol = self.protocol)
        skt_cli.send(bts+data)
        log.debug(f"error: {code}, txt={txt}")
    def connect_deal(self, skt_cli, line, headers, data_size, skt=None):
        self.record.request(line, headers, data_size)
        if data_size>0:
            dt = skt_cli.read(data_size)
            self.record.add(dt)
        self.record.finish()
        http_type, url, protocol = line
        addr = url.split(":")
        if len(addr)==1:
            addr.append(80)
        addr[1] = int(addr[1])
        addr = tuple(addr)
        code, txt = 200, "OK"
        need_close = skt is None
        if skt is None:
            try:
                skt = mhttp.WSocket.Connect(addr)
            except:
                code,txt=404,"Not Found"
        self.record.response([self.protocol,code, txt],{},0).finish()
        if code!=200:
            return self.error(skt_cli, code, txt)
        bts = mhttp.http_encode_rsp(code, txt, protocol = self.protocol)
        skt_cli.send(bts)
        try:
            self.deal_channel(skt_cli, skt)
        finally:
            if need_close:
                skt.close()
    def deal_channel(self, skt_cli, skt_srv):
        return self.direct_channel(skt_cli, skt_srv)
    def direct_channel(self, skt_cli, skt_srv):
        try:
            while True:
                while skt_cli.readable():
                    bts = skt_cli.recv(self.channel_read_size)
                    if len(bts)==0:
                        return
                    skt_srv.send(bts)
                while skt_srv.readable():
                    bts = skt_srv.recv(self.channel_read_size)
                    if len(bts)==0:
                        return
                    skt_cli.send(bts)
        except Exception as exp:
            log.debug(f"channel exp: {exp}")
            log.warn(f"traceback: {traceback.format_exc()}")
    def deal(self):
        try:
            if not self.wskt.readable():
                return True
            line, headers, data_size = mhttp.http_recv(self.wskt.rfile)
            if line is None:
                return True
            log.debug(f"[DEAL] START")
            log.debug(f"proxy recv: {line, headers, data_size}")
        except Exception as exp:
            log.warn(f"http_recv exp: {exp}")
            log.warn(f"traceback: {traceback.format_exc()}")
            return False
        http_type, url, protocol = line
        if http_type not in self.deals:
            http_type = None
        fc = self.deals[http_type]
        fc(self.wskt, line, headers, data_size)
        log.debug(f"[DEAL] END")
        return True
    def call(self):
        log.debug(f"[TESTZ] new deal")
        try:
            while True:
                if not self.deal():
                    break
        finally:
            self.wskt.close()
            #self.monitor.close()

pass

class Proxy(Base):
    def init(self, addr, listen=5, record=None):
        self.addr = addr
        self.listen = listen
        self.ths = []
        self.running=False
        if record is None:
            record = _record.MsgLog(log)
        self.record = record
    def close(self):
        self.skt.close()
    def make_dealer(self, skt, addr):
        return ProxyDealer(skt, record=self.record.clone())
    def call(self, wait_time=0.1):
        self.running=True
        skt = socket.socket()
        skt.bind(self.addr)
        skt.listen(self.listen)
        self.skt = skt
        try:
            while self.running:
                while not mhttp.readable(self.skt,wait_time):
                    pass
                skt,addr = self.skt.accept()
                deal = self.make_dealer(skt, addr)
                th = threading.Thread(target=deal,daemon=True)
                th.start()
                self.ths.append(th)
        finally:
            self.close()
