from . import itemz
class BaseDeal:
    def height_tree(self, mg, obj):
        return [1]
    def deal_encape(self, rst, conf, deep, height, up_height, left, right, top_not_format):
        left = conf.s(left)
        right = conf.s(right)
        num_spc = conf.get(line=4)
        spc = conf.s(conf.get(spc=' '))
        curr_spc = spc*(num_spc*(deep-1))
        spt = conf.s(self.spt)
        if not conf.check(format=1) or height<=conf.get(nfmt_height=1):
            spc = conf.s(" ")*conf.get(prev=0)
            spc = spt+spc
            rst = left+spc.join(rst)+right
            rst = self.prev_spc(conf, deep, up_height, top_not_format)+rst
        else:
            enter = conf.s("\n")
            rst = (spt+enter).join(rst)
            rst = left+enter+rst+enter+curr_spc+right
            if not top_not_format:
                rst = curr_spc+rst
        return rst
    def prev_spc(self, conf, deep, up_height, top_not_format):
        nfmt_height = conf.get(nfmt_height=1)
        if top_not_format:
            return conf.s("")
        if conf.check(format=1) and up_height>nfmt_height:
            num_spc = conf.get(line=4)
            spc = conf.s(conf.get(spc=' '))
            curr_spc = spc*(num_spc*(deep-1))
            return curr_spc
        return conf.s("")
    def fmt(self, s, num, spc = " "):
        spc = self.like(spc, s)
        spc = spc*num
        et = self.like("\n", s)
        arr = s.split(et)
        arr = [spc+k for k in arr]
        rs = et.join(arr)
        return rs
    def deal(self, mg, obj, up_height, heights, conf, deep, top_not_format):
        "impl"
        assert 0
    def like(self, s, target):
        if type(target) ==type(s):
            return s
        if type(s)==str:
            return s.encode()
        return s.decode()
    def __str__(self):
        return "BaseDeal"
    def __repr__(self):
        return str(self)
    def __init__(self, *argv, **maps):
        self.init(*argv, **maps)
    def init(self, *argv, **maps):
        pass