#
from buildz import Base
class MsgRecord(Base):
    """
        报文处理，非多线程安全
        要多线程安全，可以考虑：
            1，修改clone方法，新建一个MsgRecord实例而非返回self，并且自己加锁
            2，通过threading.current_thread().ident获取线程id，然后做相应处理
        需要实现的方法：
            _start: 新的请求/响应报文进来时调用，传入头部信息等
            _add: 传入报文体数据
            _add_chunk: 传入chunk数据
            _finish: 请求/响应报文数据已全部传入，看是否需要做什么处理
            实现可参考MsgLog
    """
    TypeReq ="request"
    TypeRsp = "response"
    def clone(self):
        return self
    def ssl_update(self):
        pass
    def init(self):
        self.ssl = False
        self.ssl_update()
    def set_ssl(self, ssl=True):
        '''
            声明当前连接转ssl或者从ssl转tcp，看是否需要在ssl_update做什么处理
            不管连接是ssl还是tcp，传入start，add，add_chunk方法里的数据都是明文
        '''
        self.ssl = ssl
        self.ssl_update()
    def start(self, msg_type, line, headers, data_size):
        self._start(msg_type, line, headers, data_size)
        return self
    def add(self, data):
        self._add(data)
        return self
    def add_chunk(self, data):
        self._add_chunk(data)
        return self
    def finish(self):
        self._finish()
        return self
    def request(self, line, headers, data_size):
        return self.start(MsgRecord.TypeReq, line, headers, data_size)
    def response(self, line, headers, data_size):
        return self.start(MsgRecord.TypeRsp, line, headers, data_size)
    def _start(self, msg_type, line, headers, data_size):
        """
        处理新报文数据
        line:
            msg_type==MsgRecord.TypeReq:
                line = http_type, url, protocol
            msg_type==MsgRecord.TypeRsp:
                line = protocol, code, rsp_text
            http_type: GET,POST,...
            protocol: 应该都是HTTP/1.1或HTTP/1.0
            code: 响应数据编码,200、404等
            rsp_text: 响应数据文本, OK, Not Found等
        headers: http头部信息, dict（字典）数据
        data_size: 当前报文的报文体数据大小（不包括chunk部分）
        """
        pass
    def _add(self, data):
        """
            报文体数据填充
        """
        pass
    def _add_chunk(self, data):
        """
            报文分块(chunked)传输，新增chunk数据
        """
        self._add(data)
    def _finish(self):
        """
            当前报文数据已经全部获取完成，要怎么处理可以执行了
            注：_add和_add_chunk返回的只是抓取到的报文体和块数据，如果报文体或块数据被编码和压缩了，需要自己处理解码和解压
        """
        pass

pass
class MsgLog(MsgRecord):
    def clone(self):
        return MsgLog(self.log)
    def init(self, log):
        self.log = log
        super().init()
        self.data = None
    def ssl_update(self):
        if self.ssl:
            self.log = self.log("https msg")
        else:
            self.log = self.log("http msg")
    def _start(self, msg_type, line, headers, data_size):
        self.data = [msg_type, line, headers, data_size, 0]
    def _add(self, data):
        self.data[-1]+=len(data)
    def _finish(self):
        msg_type, line, headers, data_size, real_size = self.data
        self.log.info(f"{msg_type} line:{line}, headers: {headers}, data_size: {data_size}/{real_size}")