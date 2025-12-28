'''
格式化报错
'''
class FormatExp(Exception):
    def __init__(self, err, data, s = ""):
        if len(s)==0:
            errs = "Error: {err}, line: {line}, index: {index}".format(err = err, line = data[0], index = data[1])
        else:
            errs = "Error: {err}, line: {line}, index: {index}, content: [{s}]".format(err = err, line = data[0], index = data[1], s = s)
        super(FormatExp, self).__init__(errs)

pass
