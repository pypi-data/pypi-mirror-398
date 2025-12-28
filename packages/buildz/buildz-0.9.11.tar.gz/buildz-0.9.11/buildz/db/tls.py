#
import datetime,decimal
def lower(val):
    rst = ""
    for c in val:
        if c.lower()!=c:
            c = "_"+c.lower()
        rst+=c
    return rst
pass
def upper(val):
    rst = ""
    mark_up = False
    for c in val:
        if c == "_":
            mark_up = True
            continue
        if mark_up:
            c = c.upper()
            mark_up = False
        rst+=c
    return rst
pass
def py2sql(val):
    if val is None:
        return 'null'
    if type(val)==str:
        return f"'{val}'"
    if type(val) == datetime.datetime:
        val = str(val) 
    if type(val) == decimal.Decimal:
        val = str(val)
    return val
pass