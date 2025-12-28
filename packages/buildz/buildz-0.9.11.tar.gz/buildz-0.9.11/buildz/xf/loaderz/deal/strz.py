from .. import base
from .. import item
from .. import exp
from ... import file
from ... import code as codez
from . import lr

class PrevStrDeal(lr.LRDeal):
    def types(self):
        if not self.deal_build:
            return []
        return ['str']
    def build(self, obj):
        obj.is_val = 1
        if self.translate:
            val = obj.val
            val = self.do_translate(val)
            obj.val = val
        return obj
    def prepare(self, mg):
        super().prepare(mg)
        self.as_bytes = mg.as_bytes
        self.label_l2 = mg.like("\\")
        self.label_qt = mg.like('"')
        self.label_et = mg.like("\n")
        self.label_lr = mg.like("\r")
        self.label_nl = mg.like("")
        self.et_in_right = self.right.count(self.label_et)
    def init(self, left = '"', right= '"', single_line = False, note = False, translate = False, deal_build = False):
        super().init(left, right, 'str')
        self.single_line = single_line
        self.note = note
        self.translate = translate
        self.deal_build = deal_build
        self.as_bytes = True
        self.octs = None
        self.hexs = None
    def do_translate(self, s):
        """
            取巧用python的eval来生成字符表
        """
        is_bytes = type(s)==bytes
        if is_bytes:
            return codez.ubytes(s, "utf-8")
        else:
            return codez.ub2s(s.encode("utf-8"), "utf-8")
            return codez.ustr(s)
    def deal(self, buffer, rst, mg):
        cl = buffer.read(self.ll)
        if cl != self.left:
            return False
        rm = buffer.full().strip()
        rm_pos = buffer.pos()
        buffer.clean2read(self.ll)
        if len(rm)>0:
            if not self.note:
                raise exp.Exp(f"unexcept char before string: {rm}", rm_pos)
            else:
                rst.append(item.Item(rm, rm_pos, type = "str", is_val = 0))
        tmp = cl[:0]
        ctmp = tmp[:0]
        do_judge = 1
        mark_et = 0
        mark_l2 = 0
        while True:
            if do_judge and self.right == buffer.rget(self.lr):
                break
            c = buffer.read_cache(1)
            if do_judge and c == self.label_et:
                mark_et += 1
            if len(c)==0:
                if self.single_line and self.note:
                    break
                raise exp.Exp(f"unexcept string end while reading str", buffer.pos())
            do_judge = 1
            if c == self.label_l2:
                mark_l2 = 1
                do_judge = 0
                c = buffer.read_cache(1)
                if len(c)==0:
                    raise exp.Exp(f"unexcept string end while reading str", buffer.pos())
        data = buffer.full()
        data_pos = list(buffer.pos())
        data = data[:-self.lr]
        data_pos[1]-= self.lr
        data_pos = tuple(data_pos)
        buffer.clean()
        mark_et -= self.et_in_right
        if self.single_line and mark_et>0:
            print("left:",self.left, "right:", self.right)
            raise exp.Exp(f"contain enter in single line string",data_pos)
        if self.translate and mark_l2:
            data = self.do_translate(data)
        if self.note:
            return True
        rst.append(item.Item(data, data_pos, type='str', is_val = 1))
        return True

pass
