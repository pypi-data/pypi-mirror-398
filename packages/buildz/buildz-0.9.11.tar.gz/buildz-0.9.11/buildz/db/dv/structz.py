#import pymysql
import sys
import datetime
import decimal
from buildz import logz
from buildz.db import tls
class ItDv:
    def begin(self):
        pass
    def close(self):
        pass
    def is_open(self):
        return False
    def commit(self):
        pass
    def refresh(self):
        pass
    def check_query(self, s):
        return False
    def query(self, sql, vals=()):
        # return list, first row is key
        return []
    def execute(self, sql, vals=()):
        return None
    def sql_tables(self):
        return ""

pass

class CMD:
    def begin(self):
        return self.dv.begin()
    def close(self):
        return self.dv.close()
    def __init__(self, dv, simple_format = True, log = None):
        self.s_rst = ""
        self.dv = dv
        self.simple_format = simple_format
        self.log = logz.make(log)
        self.insert_or_update = dv.insert_or_update
    def __enter__(self, *argv, **maps):
        self.dv.begin()
        return self
    def __exit__(self, *argv, **maps):
        self.dv.close()
    def exec(self, fc, *a,**b):
        need_close = False
        if not self.dv.is_open():
            self.dv.begin()
            need_close = True
        rst = fc(*a,**b)
        if need_close:
            self.dv.close()
        return rst
    def query(self, sql, vals = ()):
        return self.exec(self.dv.query, sql, vals)
    def execute(self, sql, vals = ()):
        return self.exec(self.dv.execute, sql, vals)
    def executes(self, sqls):
        if type(sqls)==str:
            sqls = sqls.split(";")
        sqls = [sql.strip() for sql in sqls if sql.strip()!=""]
        _ = [self.execute(sql) for sql in sqls]
    def s_print(self, *args):
        args = [str(k) for k in args]
        s = " ".join(args)
        s = s+"\n"
        self.s_rst += s
    def s_flush(self):
        out = self.s_rst
        self.s_rst = ""
        return out
    def rp(self, s):
        return s
        rps = ["\n\\n","\r\\r","\t\\t"]
        for rp in rps:
            s = s.replace(rp[0], rp[1:])
        return s
    def sz(self, s):
        try:
            s = s.encode("gbk")
        except Exception as exp:
            print("SZ exp:", exp)
        return min(100, len(s))
    def jstr(self, obj):
        import datetime
        import decimal
        if type(obj) == datetime.datetime:
            obj = str(obj) 
        if type(obj) == decimal.Decimal:
            obj = str(obj) 
        if type(obj) == bytes:
            for code in "utf-8,gbk".split(","):
                try:
                    obj = obj.decode(code)
                    break
                except:
                    continue
            else:
                obj = list(obj)
            #obj = list(obj)[0]
        import json
        try:
            rs = json.dumps(obj, ensure_ascii=0)
        except:
            rs = json.dumps(str(obj), ensure_ascii=0)
        return rs
    def tr_sz(self, s, sz):
        try:
            s = s.encode("gbk")
            s = s+(b" "*(sz-len(s)))
            s = s.decode("gbk")
        except Exception as exp:
            self.log.error("TR_SZ exp:", exp)
        return s
    def format(self, arr):
        arr = [[self.rp(k) for k in obj] for obj in arr]
        if self.simple_format and len(arr)>0:
            sz = [[self.sz(k) for k in obj] for obj in arr]
            l = len(arr[0])
            szs = [max([obj[i] for obj in sz]) for i in range(l)]
            arr = [[self.tr_sz(obj[i], szs[i]) for i in range(l)] for obj in arr]
        arr = [" | ".join(k) for k in arr]
        arr = ["[[ "+k+" ]]" for k in arr]
        return "\n".join(arr)
    def single(self, s):
        s=s.strip()
        if s == "commits":
            self.dv.commit()
        elif s == "reset":
            self.dv.close()
            self.dv.begin()
        elif s == "refresh":
            self.dv.refresh()
        elif s == "table":
            s = self.dv.sql_tables()
            self.s_print(self.single(s))
        elif s == "exit":
            raise Exception("exit")
        elif s.split(" ")[0] == "source":
            # source filepath [encoding]
            arr = s.split(" ")
            fp =arr[1].strip().split(";")[0]
            cd = "utf-8"
            if len(arr)>2:
                cd = arr[2].strip().lower()
            with open(fp, 'rb') as f:
                s = f.read().decode(cd)
            arr = s.split(";")
            n = len(arr)
            self.log.info(f"[TESTZ] done fread {fp}: {len(arr)}")
            i=0
            for sql in arr:
                sql=sql.replace("\r","")
                sql = sql.split("\n")
                sql = [k for k in sql if k.strip()[:2]!="--"]
                sql = "\n".join(sql)
                if sql.strip() == "" or sql.strip()[:2]=="--":
                    continue
                _sql = sql+";"
                #self.s_print("sql:", _sql)
                tmp = self.execute(_sql)
                #self.s_print(tmp)
                i+=1
            self.s_print("done source", fp)
        elif s.split(" ")[0] == "export":
            # export filepath encoding sql;
            self.s_print("export:", s)
            arr = s.split(" ")
            fp =arr[1].strip()
            cd = arr[2].strip().lower()
            s = " ".join(arr[3:])
            self.s_print("sql:", s)
            rst = self.query(s)
            result = []
            if len(rst)>0:
                keys = rst[0]
                rst = rst[1:]
                result.append(['"'+v.lower()+'"' for v in keys])
                for i, obj in zip(range(len(rst)), rst):
                    v = ['"'+str(k)+'"' for k in obj]
                    result.append(v)
            result = [", ".join(k) for k in result]
            rs = "\n".join(result)
            with open(fp, "wb") as f:
                f.write(rs.encode(cd))
            self.s_print("done write \"{s}\" to {fp}".format(s = s, fp = fp))
        elif s == "":
            return ""
        else:
            self.s_print("SQL:", s)
            try:
                tab = s.split(" ")[0]
                if tab in "tables,indexes,columns,index_keys".split(","):
                    _arr = s.split(" ")
                    _arr = [_k.strip() for _k in _arr if _k.strip()!=""]
                    _arr = _arr[1:]
                    _fc = getattr(self.dv, tab)
                    rst = self.exec(_fc, *_arr)
                    show_query = True
                elif self.dv.check_query(s):
                    rst = self.query(s)
                    show_query = True
                else:
                    rst = self.execute(s)
                    show_query = False
                if show_query:
                    result = []
                    if len(rst)>0:
                        keys = rst[0]
                        rst = rst[1:]
                        result.append(["KEY"]+keys)
                        for i, obj in zip(range(len(rst)), rst):
                            v = [self.jstr(k) for k in obj]
                            result.append([str(i)]+v)
                    self.s_print(self.format(result))
                else:
                    self.s_print(rst)
            except Exception as exp:
                import traceback
                traceback.print_exc()
                self.s_print("Error sql line:", exp)
            self.s_print("")
        return self.s_flush()
    def run(self):
        self.begin()
        try:
            while True:
                rst = []
                while True:
                    s = input(":").strip()
                    if s in "cls, clear".split(","):
                        import os
                        os.system(s)
                        continue
                    rst.append(s)
                    if s.find(";")>=0:
                        break
                s = " ".join(rst)
                s = s.split(";")[0].strip()
                if s == "exit":
                    break
                rst = self.single(s)
                print(rst)
                print("")
        finally:
            self.close()

pass
