
import sqlite3
import sys,os
from .basez import SimpleDv, fetch
from .structz import CMD
from buildz import xf,fz
from buildz.db import tls
class Db(SimpleDv):
    # func to impl:
    def to_list(self, rst):
        rows = self.cursor.description
        keys = [k[0].lower() for k in rows]
        result = []
        result.append(keys)
        if rst is None or len(rst)==0:
            return result
        result += rst
        return result
    def new_con(self):
        return sqlite3.connect(self.fp)
    def new_cursor(self):
        return self.con.cursor()
    def clone(self):
        return Db(self.fp, self.as_map)
    def __init__(self, fp, as_map=False, *argv, **maps):
        #def __init__(self, fp):
        self.con = None
        self.cursor = None
        self.as_map = as_map
        self.init(fp)
    def init(self, fp):
        fz.makefdir(fp)
        self.fp = fp
    def sql_tables(self, table = None):
        """
            if not note, use name instead
            require:
                table_name, table_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and name = '{table}'"
        return f"select name as table_name, '' as table_note from sqlite_master where type='table' {query_table};"
    def sql_indexes(self, table=None, index=None):
        """
            require:
                table_name, index_name, is_unique, index_type, index_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and tbl_name = '{table}'"
            if index is not None:
                query_table+= f" and name='{index}'"
        return f"select tbl_name as table_name, name as index_name, -1 as is_unique, '?' as index_type, '' as index_note from sqlite_master where type='index' {query_table};"
    def columns(self, table, as_map=None):
        """
            require:
                table_name, column_name, column_type, column_default, nullable, column_offset, column_note
        """
        rst = self.query(f"PRAGMA table_info({table})", as_map=0)
        dts = rst[1:]
        keys = "table_name, column_name, column_type, column_default, nullable, column_offset, column_note".split(", ")
        rst = [keys]
        for dt in dts:
            cid, name, _type, notnull, dflt_value, pk = dt
            tmp = [table, name, _type, dflt_value, notnull, cid, '']
            rst.append(tmp)
        rst = self.out_list_sqlite3(rst, as_map)
        return rst
    def index_keys(self, table, index, as_map=None):
        """
            require:
                table_name, index_name, column_name, index_offset, column_note
        """
        rst = self.query(f"PRAGMA index_info({index})", as_map=0)
        dts = rst[1:]
        keys = "table_name, index_name, column_name, index_offset, column_note".split(", ")
        rst = [keys]
        for dt in dts:
            seqno, cid, name = dt
            tmp = [table, index, name, seqno, '']
            rst.append(tmp)
        return self.out_list_sqlite3(rst, as_map)
    def out_list_sqlite3(self, query_result, as_map=None):
        if as_map is None:
            as_map = self.as_map
        rst = query_result
        if as_map and len(rst)>0:
            if len(rst)==1:
                return []
            keys = rst[0]
            rst = rst[1:]
            rst = [{k:v for k,v in zip(keys, dt)} for dt in rst]
        return rst
    def iou_sql(self, table, ks, vs, sets, qs):
        if len(qs)==0:
            sql = f"insert into {table}({ks}) values({vs})"
        else:
            sql = f"insert into {table}({ks}) values({vs}) ON CONFLICT({','.join(qs)}) DO UPDATE SET {sets}"
        return sql
    def insert_or_updatexxx(self, maps, table, keys = None, update_keys = None):
        if type(maps)!=dict:
            maps = maps.__dict__
        if keys is None:
            keys = []
        if type(keys) not in (list, tuple):
            keys = [keys]
        kvs = [[k,tls.py2sql(v)] for k,v in maps.items()]
        sets = [f"{k}={v}" for k,v in kvs if update_keys is None or k in update_keys]
        sets = ",".join(sets)
        ks = ",".join([kv[0] for kv in kvs])
        vs = ",".join([str(kv[1]) for kv in kvs])
        sql = f"insert into {table}({ks}) values({vs}) ON CONFLICT DO UPDATE SET {sets}"
        #print(f"[TESTZ] sql: {sql}")
        return self.execute(sql)

pass
def build(argv, conf):
    root = xf.g(conf, root=None)
    fp = argv[0]
    if root is not None:
        fp = os.path.join(root, fp)
    as_map = xf.g(conf, as_map=False)
    dv = Db(fp, as_map)
    return dv
def buildbk(argv, conf):
    return CMD(make(argv, conf))

pass
