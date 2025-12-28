import sys
from .structz import ItDv
from buildz.db import tls
from buildz import xf
def sp(obj):
    return super(obj.__class__, obj)

pass
class SimpleDv(ItDv):
    # func to impl:
    def to_list(self, query_result):
        return []
    def sql_tables(self, table = None):
        """
            if not note, use name instead
            require:
                table_name, table_note
        """
        raise Exception("unimplement")
        return None
    def sql_columns(self, table):
        """
            require:
                table_name, column_name, column_type, column_default, nullable, column_offset, column_note
        """
        raise Exception("unimplement")
        return None
    def sql_indexes(self, table=None):
        """
            require:
                table_name, index_name, is_unique, index_type, index_note
        """
        raise Exception("unimplement")
        return None
    def sql_index_keys(self, table, index):
        """
            require:
                table_name, index_name, column_name, index_offset, column_note
        """
        raise Exception("unimplement")
        return None
    def new_con(self):
        return None
    def new_cursor(self):
        return None
    def init(self, *argv, **maps):
        pass
    def tables(self, table=None, as_map=None):
        sql = self.sql_tables(table)
        return self.query(sql, as_map=as_map)
    def columns(self, table, as_map=None):
        sql = self.sql_columns(table)
        return self.query(sql, as_map=as_map)
    def indexes(self, table=None, index=None, as_map=None):
        sql = self.sql_indexes(table, index)
        return self.query(sql, as_map=as_map)
    def index_keys(self, table, index, as_map=None):
        sql = self.sql_index_keys(table, index)
        return self.query(sql, as_map=as_map)
    # func already impl
    def check_query(self, s):
        arr = s.split(" ")
        k = arr[0].strip().lower()
        rst = k not in "delete,insert,update,create,drop,commit,alter".split(",")
        return rst
    def out_list(self, query_result, as_map=None):
        if as_map is None:
            as_map = self.as_map
        rst = self.to_list(query_result)
        if as_map and len(rst)>0:
            if len(rst)==1:
                return []
            keys = rst[0]
            rst = rst[1:]
            rst = [{k:v for k,v in zip(keys, dt)} for dt in rst]
        return rst
    def clone(self):
        return type(self)(self.host, self.port, self.user, sel.pwd, self.db, self.as_map, *self.argv, **self.maps)
    def __init__(self, host, port, user, pwd, db, as_map=False, *argv, **maps):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db = db
        self.con = None
        self.cursor = None
        self.as_map = as_map
        self.argv = argv
        self.maps = maps
        self.init(*argv, **maps)
    def begin(self):
        if self.con is not None:
            return
        self.con = self.new_con()
        self.cursor = self.new_cursor()
    def open(self):
        self.begin()
    def close(self):
        self.cursor.close()
        self.con.close()
        self.cursor = None
        self.con = None
    def is_open(self):
        return self.cursor is not None
    def commit(self):
        self.cursor.close()
        self.con.commit()
        self.cursor = self.new_cursor()
    def refresh(self):
        self.cursor.close()
        self.cursor = self.new_cursor()
    def query(self, sql, vals=(), as_map = None):
        # return list, first row is key
        tmp = self.cursor.execute(sql, vals)
        #print("[TESTZ] exe:",tmp)
        rst = self.cursor.fetchall()
        return self.out_list(rst, as_map)
    def executes(self, sqls, commit=False):
        if type(sqls)==str:
            sqls = sqls.split(";")
        sqls = [sql.strip() for sql in sqls if sql.strip()!=""]
        _ = [self.execute(sql) for sql in sqls]
        if commit:
            self.execute("commit;")
    def execute(self, sql, vals=(), commit=False):
        #print(f"[TESTZ] sql: {sql}")
        tmp = self.cursor.execute(sql, vals)
        if commit:
            self.cursor.execute("commit;")
        return tmp
    def iou_sql(self, table, ks, vs, sets, qs):
        if len(sq)==0:
            sql = f"insert into {table}({ks}) values({vs})"
        else:
            sql = f"insert into {table}({ks}) values({vs}) on duplicate key update {sets}"
        return sql
    def insert_or_update(self, maps, table, keys = None, update_keys = None):
        if type(update_keys)==str:
            update_keys = [update_keys]
        if type(maps)!=dict:
            maps = maps.__dict__
        if keys is None:
            keys = []
        if type(keys) not in (list, tuple):
            keys = [keys]
        # update = False
        # conds = ""
        # if len(keys)>0:
        #     need_query = True
        #     conds = []
        #     for k in keys:
        #         if k not in maps:
        #             need_query = False
        #             break
        #         v = maps[k]
        #         if type(v)==str:
        #             v = f"'{v}'"
        #         if v is not None:
        #             cond = f"{k} = {v}"
        #         else:
        #             cond = f"{k} is null"
        #         conds.append(cond)
        #     if need_query:
        #         conds = " and ".join(conds)
        #         sql_search = f"select count(*) from {table} where {conds}"
        #         rst = self.query(sql_search, as_map = False)[1][0]
        #         update = rst>0
        kvs = [[k,tls.py2sql(v)] for k,v in maps.items()]
        #print(f"[TESTZ] save kvs: {kvs}, update_keys: {update_keys}")
        sets = [f"{k}={v}" for k,v in kvs if update_keys is None or k in update_keys]
        sets = ",".join(sets)
        ks = ",".join([kv[0] for kv in kvs])
        vs = ",".join([str(kv[1]) for kv in kvs])
        sql = self.iou_sql(table, ks, vs, sets, keys)
        #sql = f"insert into {table}({ks}) values({vs}) on duplicate key update {sets}"
        return self.execute(sql)
        if update:
            keys = set(keys)
            kvs = [[k,tls.py2sql(v)] for k,v in maps.items() if k not in keys]
            sets = [f"{k}={v}" for k,v in kvs]
            sets = ",".join(sets)
            sql = f"update {table} set {sets} where {conds}"
        else:
            kvs = [[k,tls.py2sql(v)] for k,v in maps.items()]
            ks = ",".join([kv[0] for kv in kvs])
            vs = ",".join([str(kv[1]) for kv in kvs])
            sql = f"insert into {table}({ks}) values({vs})"
        return self.execute(sql)

pass

# user|pwd@host:port/db
def fetch(args, conf={}):
    """
        host[:port][/db][ user][ pwd]
        host:port/db user pwd
    """
    if type(args) == str:
        args = args.split(" ")
    url = args[0].strip()
    tmp = url.split("/")
    url = tmp[0]
    db = None
    if len(tmp)>1:
        db = tmp[1]
    tmp = url.split(":")
    if len(tmp)==2:
        host, port = tmp
        port = int(port)
    else:
        host = tmp[0]
        port = None
    user = None
    if len(args)>1:
        user = args[1]
        if user is not None:
            user = user.strip()
    pwd = None
    if len(args)>2:
        pwd = args[2]
        if pwd is not None:
            pwd = pwd.strip()
    as_map = xf.g(conf, as_map=False)
    return host, port, user, pwd, db, as_map

pass