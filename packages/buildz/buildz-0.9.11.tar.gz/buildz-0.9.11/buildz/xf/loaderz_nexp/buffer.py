
class BufferInput:
    def __init__(self, buf):
        self.buf = buf
    def __call__(self, size=1):
        s = self.buf[:size]
        self.buf = self.buf[size:]
        return s

pass

class Buffer:
    def read_cache(self, size = 1):
        s = self.read(size)
        self.buffer+=s
        self.s_read = self.s_read[len(s):]
        return s
    def read(self, size = 1):
        if self.s_read is None:
            self.s_read = self.input(1)
        l = len(self.s_read)
        if l<size:
            self.s_read += self.input(size-l)
        rst = self.s_read[:size]
        if self.buffer is None:
            self.buffer = self.s_read[:0]
        return rst
    def clean2read(self, size = 1):
        self.s_read = self.s_read[size:]
        self.clean()
    def init(self):
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
    def clean(self):
        self.buffer = self.buffer[:0]
    def rget(self, size=1):
        return self.buffer[-size:]
    def get(self, size=1):
        return self.buffer[:size]

pass

class StrBuffer:
    def read_cache(self, size = 1):
        s = self.read(size)
        l = len(s)
        self.buffer_size+=l
        self.read_base+=l
        return s
    def read(self, size = 1):
        s = self.str[self.read_base:self.read_base+size]
        return s
    def clean2read(self, size = 1):
        self.read_base+=size
        self.clean()
    def init(self):
        self.buffer_base = 0
        self.buffer_size = 0
        self.read_base = 0
        self.read_size = 0
        #self.buffer = None
        #self.s_read = None
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
    def clean(self):
        self.buffer_base = self.read_base
        self.buffer_size = 0
    def rget(self, size=1):
        size = min(size, self.buffer_size)
        return self.str[self.buffer_base+self.buffer_size-size:self.buffer_base+self.buffer_size]
    def get(self, size=1):
        size = min(size, self.buffer_size)
        return self.str[self.buffer_base:self.buffer_base+size]

pass
