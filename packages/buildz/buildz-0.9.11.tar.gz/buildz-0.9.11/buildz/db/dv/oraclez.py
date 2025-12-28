
import os
import sys
dp = os.path.dirname(__file__)
gdp = os.path.join(dp, "lib")

def init_path(dp):
    path = os.environ["PATH"] 
    if sys.platform.lower().find("win")>=0:
        cb = ";"
    else:
        cb = ":"
    path = path +cb+dp
    os.environ["PATH"] = path

pass

#init_path(dp)
import sys
from .basez import SimpleDv, fetch
from .structz import CMD
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
        if self.port is not None:
            add = ":"+str(self.port)
        else:
            add = ""
        try:
            import cx_Oracle as pymysql
        except ModuleNotFoundError:
            raise Exception("module not found, try: pip install cx-Oracle")
        return pymysql.connect(self.user, self.pwd, self.host+add+"/"+self.db)
    def new_cursor(self):
        return self.con.cursor()
    def init(self, *argv, **maps):
        pass
    def sql_tables(self, table = None):
        """
            if not note, use name instead
            require:
                table_name, table_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and t.table_name = '{table.upper()}'"
        return f"select t.table_name as table_name, tc.comments as table_note from all_tables t inner join all_tab_comments tc on t.table_name=tc.table_name where t.owner='{self.user.upper()}' {query_table}"
    def sql_columns(self, table):
        """
            require:
                table_name, column_name, column_type, column_default, nullable, column_offset, column_note
        """
        return f"select c.table_name as table_name, c.column_name as column_name, c.data_type|| '(' ||c.data_length||','||c.data_precision||','||c.data_scale||')' as column_type, c.data_default as column_default, c.nullable as nullable, c.column_id as column_offset, cc.comments as column_note from all_tab_columns c inner join all_col_comments cc on c.column_name=cc.column_name and c.table_name=cc.table_name where c.table_name='{table.upper()}' order by c.column_id asc"
    def sql_indexes(self, table=None, index=None):
        """
            require:
                table_name, index_name, is_unique, index_type, index_note
        """
        query_table = ""
        if table is not None:
            query_table =  f" and table_name = '{table.upper()}'"
            if index is not None:
                query_table+= f" and index_name='{index.upper()}'"
        return f"select table_name, index_name,  case uniqueness when 'UNIQUE' then 1 else 0 end as is_unique, index_type, '' as index_note from all_indexes where owner = '{self.user.upper()}'{query_table}"
    def sql_index_keys(self, table, index):
        """
            require:
                table_name, index_name, column_name, index_offset, column_note
        """
        return f"select table_name, index_name, column_name, column_position as index_offset, '' as note from all_ind_columns where index_name='{index.upper()}' and table_name='{table.upper()}' order by column_position asc"

pass
def build(argv, conf):
    k = 'oracle_lib'
    dp = gdp
    if k in conf:
        dp = conf[k]
    init_path(dp)
    #print(f"oracle lib: {dp}")
    dv = Db(*fetch(argv))
    return dv
def buildbk(argv, conf):
    return CMD(make(argv, conf))

pass
