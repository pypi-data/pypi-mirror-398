#
from . import fio
def to_csv(keys, cols, fp):
    assert len(keys)==len(cols)
    fio.makefdir(fp)
    keys = ", ".join(keys)
    rst = [keys]
    for tmp in zip(*cols):
        tmp = [str(k) for k in tmp]
        tmp = ", ".join(tmp)
        rst.append(tmp)
    rs = "\n".join(rst)
    fio.write(rs.encode("utf-8"), fp)

pass

def from_csv(fp, col=True, as_map = False):
    # 好像还没测试
    s = fio.read(fp).decode("utf-8")
    arr = s.split("\n")
    arr = [[v.strip() for v in k.split(",")] for k in arr if k.strip()!=""]
    keys = arr[0]
    datas = arr[1:]
    if col:
        datas = []
        for i in range(len(keys)):
            tmp = [k[i] for k in datas]
            datas.append(tmp)
        if as_map:
            datas = {k:arr for k,arr in zip(keys, datas)}
    elif as_map:
        datas = [{k:v for k,v in zip(keys, dt)} for dt in datas]
    return keys, datas

pass

