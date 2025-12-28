try:
    import psycopg
except ModuleNotFoundError:
    try:
        import psycopg2 as psycopg
    except ModuleNotFoundError:
        raise Exception("module not found, try: pip install psycopg")
import sys
from .basez import SimpleDv, fetch
from .structz import CMD
class Db(SimpleDv):
    # func to impl:
    def to_list(self, rst):
        rows = self.cursor.description
        keys = [k.name.lower() for k in rows]
        result = []
        result.append(keys)
        if rst is None or len(rst)==0:
            return result
        result += rst
        return result
    def new_con(self):
        return psycopg.connect(host=self.host, 
            port = self.port, user =self.user, 
            password =self.pwd, dbname = self.db)
    def new_cursor(self):
        return self.con.cursor()
    def init(self, *argv, **maps):
        if self.port is None:
            self.port = 5432
        if self.user is None:
            self.user = "postgres"
        pass

pass
def build(argv, conf):
    dv = Db(*fetch(argv))
    return dv
def buildbk(argv, conf):
    return CMD(make(argv, conf))

pass
