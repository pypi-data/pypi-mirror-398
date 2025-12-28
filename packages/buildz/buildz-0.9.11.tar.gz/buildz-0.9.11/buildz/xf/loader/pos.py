

class PosCal:
    def __init__(self):
        self.init()
    def init(self):
        self.sizes = [0]
    def cal_offset(self, s):
        n = "\n"
        r = "\r"
        ep = ""
        if type(s)==bytes:
            n = b"\n"
            r = b"\r"
            ep = b""
        s = s.replace(n, ep).replace(r, ep)
        return -len(s)
    def update(self, s):
        #print("update:["+s+"]")
        szs = self.sizes
        n = "\n"
        r = "\r"
        ep = ""
        if type(s)==bytes:
            n = b"\n"
            r = b"\r"
            ep = b""
        arr = s.replace(r, ep).split(n)
        szs[-1]+=len(arr[0])
        arr = arr[1:]
        for v in arr:
            szs.append(len(v))
            #szs[-1]+=len(v)
    def get(self, offset=0):
        #print("cal get:", offset, self.sizes)
        if type(offset) in [bytes, str]:
            offset = -self.cal_offset(offset)
        offset = -offset
        szs = self.sizes
        row = len(szs)-1
        col = szs[row]
        while offset>0 and row>0:
            sz = szs[row]
            if sz >= offset:
                col = sz-offset
                break
            offset -= sz+1
            row -= 1
            col = szs[row]
        #print("cal result:", row, col)
        return [row+1, col+1]