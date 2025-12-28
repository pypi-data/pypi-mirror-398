'''
格式化报错
'''
class FormatExpBak(Exception):
    def __init__(self, err, data, s = ""):
        if len(s)==0:
            errs = "Error: {err}, line: {line}, index: {index}".format(err = err, line = data[0], index = data[1])
        else:
            errs = "Error: {err}, line: {line}, index: {index}, content: [{s}]".format(err = err, line = data[0], index = data[1], s = s)
        super(FormatExp, self).__init__(errs)

pass

class Exp(Exception):
    def __init__(self, msg, pos):
        msg = f"{msg}, [OFFSET]: {pos}"
        self.pos = pos
        super().__init__(msg)

pass

def deal(exp, buff):
    pos_str = buff.pos2str(exp.pos)
    s = str(exp)
    msg = f"{s} [CONTENT]: '{pos_str}'"
    raise Exception(msg)