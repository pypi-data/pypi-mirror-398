#coding=utf-8
from buildz import xf, argx, pyz, ioc, fz,tz

from ..test import text_sfx, args, maps
class Deal:
    def deal(self):
        if len(args)<5:
            print("need opt, file1, file2, step_file")
            return
        opt = args[1]
        fp1 = args[2]
        fp2 = args[3]
        if len(args)>4:
            fp_step = args[4]
        else:
            fp_step = "steps.diff"
        mark_encode = argx.get(maps, 'e', 1)
        mark_txt = argx.get(maps, 't', None)
        if mark_txt:
            mark_encode = 0
        spt = argx.get(maps, 's', 1)
        nspt = argx.get(maps, 'ns', 0)
        if nspt:
            spt = 0
        if opt == 'diff' or opt == 'count':
            bs1 = fz.read(fp1).decode("utf-8")
            bs2 = fz.read(fp2).decode("utf-8")
            #bs1 = b"text z xxxyzijsa"
            #bs2 = b"test xxxx afzjcovijsax"
            stps = tz.m_steps(bs1, bs2,split=spt)
            if opt == 'count':
                cnt = tz.m_count(stps)
                print(f"diff from {fp1} to {fp2}: {cnt}")
                return
            if mark_encode:
                stps = b"e"+tz.m_encode(stps)
            else:
                for stp in stps:
                    c = stp[-1]
                    if type(c)==bytes:
                        stp[-1] = c.decode()
                stps = "t"+xf.dumps(stps)
                stps = stps.encode()
            fz.write(stps, fp_step)
            print("done diff")
        elif opt == 'update':
            bs1 = fz.read(fp1).decode("utf-8")
            bs_step = fz.read(fp_step)
            mark_encode = bs_step[:1] == b'e'
            bs_step= bs_step[1:]
            if mark_encode:
                stps = tz.m_decode(bs_step)
            else:
                stps = xf.loads(bs_step.decode())
            bs2 = tz.m_update(bs1, stps,split=spt).encode("utf-8")
            fz.write(bs2, fp2)
            print("done update")
        else:
            print(f"unexpect opt: {opt}")
    pass

pass
