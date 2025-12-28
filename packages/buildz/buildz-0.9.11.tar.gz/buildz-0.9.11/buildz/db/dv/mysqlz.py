try:
    import pymysql
except ModuleNotFoundError:
    raise Exception("module not found, try: pip install pymysql")
import sys
from .basez import SimpleDv, fetch
from .structz import CMD
class Db(SimpleDv):
    # func to impl:
    def to_list(self, rst):
        result = []
        if rst is None or len(rst)==0:
            return result
        a = rst[0]
        keys = list(a.keys())
        result.append(keys)
        for obj in rst:
            v = [obj[k] for k in keys]
            result.append(v)
        return result
    def new_con(self):
        return pymysql.connect(host=self.host, 
            port = self.port, user =self.user, 
            password =self.pwd, database = self.db,
            charset='utf8',init_command="SET SESSION time_zone='+08:00'")
    def new_cursor(self):
        return self.con.cursor(pymysql.cursors.DictCursor)
    def init(self, *argv, **maps):
        if self.port is None:
            self.port = 3306
        pass
    def sql_tables(self, table = None):
        """
            if not note, use name instead
            require:
                table_name, table_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and table_name = '{table}'"
        return f"select table_name, table_comment as table_note from information_schema.tables where table_schema='{self.db}' {query_table};"
    def sql_columns(self, table):
        """
            require:
                table_name, column_name, column_type, column_default, nullable, column_offset, column_note
        """
        return f"select table_name, column_name, column_type, column_default, is_nullable as nullable, ordinal_position as column_offset, column_comment as column_note from information_schema.columns where table_schema='{self.db}' and table_name = '{table}' order by ordinal_position asc;"
    def sql_indexes(self, table=None, index=None):
        """
            require:
                table_name, index_name, is_unique, index_type, index_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and table_name = '{table}'"
            if index is not None:
                query_table+= f" and index_name='{index}'"
        return f"select table_name, index_name, 1-any_value(non_unique) as is_unique, any_value(index_type) as index_type, any_value(index_comment) as index_note from information_schema.statistics where table_schema='{self.db}' {query_table} group by index_name;"
    def sql_index_keys(self, table, index):
        """
            require:
                table_name, index_name, column_name, index_offset, column_note
        """
        return f"select table_name, index_name, column_name, seq_in_index as index_offset, comment as column_note from information_schema.statistics where table_name='{table}' and table_schema='{self.db}' and index_name = '{index}' order by seq_in_index asc;"

pass
def build(argv, conf):
    dv = Db(*fetch(argv))
    return dv
def buildbk(argv, conf):
    return CMD(make(argv, conf))

pass
