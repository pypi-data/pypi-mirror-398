
try:
    import clickhouse_driver
except ModuleNotFoundError:
    raise Exception("module not found, try: pip install clickhouse-driver")
from clickhouse_driver import connect
from clickhouse_driver import Client
import sys
from .basez import SimpleDv, fetch
from .structz import CMD
class Db(SimpleDv):
    # func to impl:
    def query(self, sql, vals={}, as_map = None):
        assert len(vals)==0
        return super().query(sql, {}, as_map)
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
        return connect('clickhouse://{user}:{pwd}@{host}:{port}/{db}'.format(user = self.user, db = self.db, pwd =self.pwd, host = self.host, port = self.port))
    def new_cursor(self):
        return self.con.cursor()
    def init(self, *argv, **maps):
        pass

pass
def build(argv, conf):
    dv = Db(*fetch(argv))
    return dv
def buildbk(argv, conf):
    return CMD(make(argv, conf))

pass
