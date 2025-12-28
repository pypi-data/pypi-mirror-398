#

def build(dv,*a,**b):
    if dv == 'mysql':
        from .mysqlz import build as _build
    elif dv == 'oracle':
        from .oraclez import build as _build
    elif dv == 'clickhouse':
        from .clickhousez import build as _build
    elif dv == "postgresql":
        from .postgresqlz import build as _build
    elif dv == "sqlite3":
        from .sqlite3z import build as _build
    else:
        raise Exception(f"not impl dv: {dv}")
    return _build(*a, **b)

pass
    

