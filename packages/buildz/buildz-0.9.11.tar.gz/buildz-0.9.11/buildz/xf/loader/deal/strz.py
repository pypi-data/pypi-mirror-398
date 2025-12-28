from .. import base
from .. import item
from .. import exp
from ... import file
import json
class PrevStrDeal(base.BaseDeal):
    def has_prev(self):
        return 1
    def has_deal(self):
        return 0
    def init(self, left = '"', right= '"', single_line = False, note = False, translate = False):
        self.left = left
        self.right = right
        self.ll = len(left)
        self.lr = len(right)
        self.single_line = single_line
        self.note = note
        self.translate = translate
    def json_loads(self, s):
        x = s
        cd = None
        if type(x)==bytes:
            x, cd = file.decode_c(x)
        rs = json.loads(x)
        if type(s)==bytes:
            rs = rs.encode(cd)
        return rs
    def do_translate(self, s):
        """
            取巧直接调用json
        """
        qt = self.like('"',s)
        ql = self.like("\\", s)
        et = self.like("\n", s)
        tr = self.like("\r", s)
        nt = self.like("",s)
        pt = ql+qt
        arr = s.split(pt)
        arr = [k.replace(qt, pt) for k in arr]
        s = pt.join(arr)
        #s = s.replace(qt, ql+qt)
        s = s.replace(tr, nt)
        arr = s.split(et)
        outs = [self.json_loads(qt+k+qt) for k in arr]
        outs = et.join(outs)
        return outs
    def prev(self, buffer, queue, pos):
        cl = buffer.read(self.ll)
        if not self.same(self.left, cl):
            return False
        buffer.pop_read(self.ll)
        rm = buffer.full()
        rm_pos = pos.get()
        if len(rm.strip())>0 and not self.note:
            print("left:", self.left, rm)
            raise exp.FormatExp("unexcept char before string", pos.get(), rm)
        pos.update(rm)
        pos.update(cl)
        buffer.clean()
        tmp = cl[:0]
        ctmp = tmp[:0]
        while True:
            if self.same(self.right, ctmp[-self.lr:]):
                break
            c = buffer.read(1,1)
            if len(c)==0:
                pos.update(tmp)
                raise exp.FormatExp("unexcept file end while reading string", pos.get())
            tmp += c
            if self.same("\\", c):
                c = buffer.read(1,1)
                if len(c)==0:
                    pos.update(tmp)
                    raise exp.FormatExp("unexcept file end while reading string", pos.get())
                tmp += c
                continue
            ctmp+=c
        buffer.clean()
        xtmp = tmp[:-self.lr]
        if not self.note and self.single_line and xtmp.find(self.like("\n", xtmp))>=0:
            print("left:",self.left, "right:", self.right)
            raise exp.FormatExp("contain enter in single line string", pos.get(), tmp)
        if self.translate:
            xtmp = self.do_translate(xtmp)
        curr_pos = pos.get()
        pos.update(tmp)
        if self.note:
            if len(rm)>0:
                queue.append(item.PrevItem(rm.rstrip(), rm_pos, is_val = 1, src='str'))
            return True
        queue.append(item.PrevItem(xtmp, curr_pos, self.id(), is_val = 1, src='str'))
        return True

pass
