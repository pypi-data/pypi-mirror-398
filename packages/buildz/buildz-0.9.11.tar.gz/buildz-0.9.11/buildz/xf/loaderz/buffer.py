
class BufferInput:
    def __init__(self, buf):
        self.buf = buf
    def __call__(self, size=1):
        s = self.buf[:size]
        self.buf = self.buf[size:]
        return s

pass
"""
Buffer:
    缓存操作:
        //add：从数据中获取字符串并直接放入缓存，返回空
        get: 从缓存获取字符串
        rget: 从缓存获取字符串，从右往左拿
        size: 缓存大小
        clean: 清空缓存
        full：获取缓存完整字符串
        read_cache: 从数据中获取字符串并直接放入缓存，返回获取的字符串
    操作数据
        read: 从数据中获取字符串
        clean2read：清空缓存和数据中所有读取过的字符串
    pos: 返回缓存索引，数据读取索引
"""
class BufferBase:
    def pos2str(self, pos):
        assert 0
    def init(self):
        self.buffer_base =0
        self.read_base=0
    def pos(self):
        return self.buffer_base, self.buffer_base+self.size()
    def offsets(self):
        return self.buffer_base, self.read_base
    def read_cache(self, size=1):
        assert 0
    def read(self, size=1):
        assert 0
    def clean2read(self, size=1):
        return self.clean(size)
    def clean(self, read_size=0):
        assert 0
    def size(self):
        assert 0
    def full(self):
        assert 0
    def rget(self, size=1):
        assert 0
    def get(self, size=1):
        assert 0
class Buffer(BufferBase):
    def pos2str(self, pos):
        return "read from file"
    def read_cache(self, size = 1):
        s = self.read(size)
        self.buffer+=s
        self.s_read = self.s_read[len(s):]
        return s
    def read(self, size = 1):
        if self.s_read is None:
            self.s_read = self.input(1)
            self.read_base+=1
        l = len(self.s_read)
        if l<size:
            self.s_read += self.input(size-l)
            self.read_base+=size-l
        rst = self.s_read[:size]
        if self.buffer is None:
            self.buffer = self.s_read[:0]
        return rst
    def init(self):
        super().init()
        self.buffer = None
        self.s_read = None
    def __init__(self, input):
        self.input = input
        self.init()
    def add(self, size):
        if self.buffer is None:
            self.buffer = self.s_read[:size]
        else:
            self.buffer += self.s_read[:size]
    def size(self):
        if self.buffer is None:
            return 0
        return len(self.buffer)
    def full(self, size = 0, right = 1):
        return self.buffer
    def clean2read(self, read_size=1):
        if read_size>0:
            self.s_read = self.s_read[read_size:]
        self.buffer = self.buffer[:0]
        self.buffer_base=self.read_base
    def clean(self, read_size = 0):
        if read_size>0:
            self.s_read = self.s_read[read_size:]
        self.buffer = self.buffer[:0]
        self.buffer_base=self.read_base
    def rget(self, size=1):
        return self.buffer[-size:]
    def get(self, size=1):
        return self.buffer[:size]

pass

def decode(s, coding = 'utf-8'):
    coding = coding.lower()
    xcoding = 'utf-8'
    if coding == 'utf-8':
        xcoding = 'gbk'
    try:
        return s.decode(coding)
    except:
        return s.decode(xcoding)

pass
class StrBuffer(BufferBase):
    def pos2str(self, pos):
        s = self.str[pos[0]:pos[1]+1]
        return s
    def read_cache(self, size = 1):
        s = self.read(size)
        l = len(s)
        self.buffer_size+=l
        self.read_base+=l
        return s
    def read(self, size = 1):
        s = self.str[self.read_base:self.read_base+size]
        if type(s)==bytes:
            s = decode(s)
        return s
    def init(self):
        super().init()
        self.buffer_size = 0
    def __init__(self, s):
        self.str = s
        self.init()
    def add(self, size):
        # x = self.str[self.buffer_base+self.buffer_size:self.buffer_base+self.buffer_size+len(arr)]
        # if x!=arr:
        #     print(f"[ERROR] x:({x}), arr:({arr}), bb: {self.buffer_base}, bs:{self.buffer_size}, rb: {self.read_base}")
        #     print("[["+self.str[self.buffer_base:self.read_base+10]+"]]")
        #     raise Exception("")
        self.buffer_size+=size
    def size(self):
        return self.buffer_size
    def full(self):
        return self.str[self.buffer_base:self.buffer_base+self.buffer_size]
    def clean2read(self, read_size=1):
        self.read_base+=read_size
        self.buffer_base = self.read_base
        self.buffer_size = 0
    def clean(self, read_size = 0):
        self.read_base+=read_size
        self.buffer_base = self.read_base
        self.buffer_size = 0
    def rget(self, size=1):
        size = min(size, self.buffer_size)
        return self.str[self.buffer_base+self.buffer_size-size:self.buffer_base+self.buffer_size]
    def get(self, size=1):
        size = min(size, self.buffer_size)
        return self.str[self.buffer_base:self.buffer_base+size]

pass
