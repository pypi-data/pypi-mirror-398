import uuid
from functools import wraps

from delta.tables import *
from pyspark.sql import SparkSession as _s
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

from .common import *

_APP = "NDS"
_NDS_PREFIX = "spark"
_HADOOP = f"{_NDS_PREFIX}.hadoop"
_SQL = f"{_NDS_PREFIX}.sql"
_BRICKS = f"{_NDS_PREFIX}.databricks"
_FMT = "delta"
_SCHEMA = "overwriteSchema"
_builder = _s.builder
_instance = None


def nds_extern_call(f):
    @wraps(f)
    def _deco(*k, **kw):
        return f(*k, **kw)
    return _deco


def nds_import_data(data):
    assert _instance is not None

    if hasattr(data, "schema"):
        return data

    if isinstance(data, dict):
        data = [data]

    return _instance.createDataFrame([{
        k: (v if v is not None else "") for k, v in fields.items()
    } for fields in data])


def _exist_table(table):
    assert _instance is not None
    try:
        return _instance.table(table)
    except:
        return False


def nds_list_tables():
    assert _instance is not None
    return [t.name for t in _instance.catalog.listTables()]


@nds_extern_call
def nds_describe_table(table):
    assert _instance is not None
    data = _instance.table(table)
    return [{
        "col_name": f.name,
        "data_type": str(f.dataType),
    } for f in data.schema.fields]


def nds_temp_view(table):
    return f"{table}_{uuid.uuid4().hex[:8]}"


def _write(table, data, mode="overwrite", schema="true"):
    data.write.mode(mode).option(
        _SCHEMA, schema).format(_FMT).saveAsTable(table)


def _keys(keys):
    return " AND ".join([f"d.{k}=s.{k}" for k in keys])


def _refresh(table, data, keys):
    assert _instance is not None
    (DeltaTable.forName(_instance, table)
        .alias("d").merge(data.alias("s"), _keys(keys))
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
     )


def nds_refresh(table, data, keys):
    data = nds_import_data(data)
    return _refresh(table, data, keys) if _exist_table(table) else _write(table, data)


def nds_query(table, fields, start, end, sqlwhere):
    assert _instance is not None
    data = _instance.table(table)

    if fields.strip() == "*":
        field_list = data.columns
    else:
        field_list = [f.strip() for f in fields.split(",")]
    data = data.select(*field_list)

    if sqlwhere:
        data = data.filter(expr(sqlwhere))

    data = data.orderBy(col(field_list[0]))
    return [r.asDict() for r in data.offset(start-1).limit(end-start+1).collect()]


def _setup(b):
    url, username, password = nds_split_url("URL")
    ep, ak, sk = nds_split_url("EP")

    return (b
            .appName(_APP)
            .config(f"{_HADOOP}.fs.s3a.endpoint", ep)
            .config(f"{_HADOOP}.fs.s3a.access.key", ak)
            .config(f"{_HADOOP}.fs.s3a.secret.key", sk)
            .config(f"{_HADOOP}.fs.s3a.path.style.access", "true")
            .config(f"{_SQL}.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(f"{_SQL}.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config(f"{_SQL}.warehouse.dir", "s3a://emdm/project")
            .config(f"{_SQL}.sources.default", _FMT)
            .config(f"{_HADOOP}.fs.defaultFS", "s3a://emdm")
            .config(f"{_HADOOP}.javax.jdo.option.ConnectionDriverName", "org.postgresql.Driver")
            .config(f"{_HADOOP}.javax.jdo.option.ConnectionURL", url)
            .config(f"{_HADOOP}.javax.jdo.option.ConnectionUserName", username)
            .config(f"{_HADOOP}.javax.jdo.option.ConnectionPassword", password)
            .config(f"{_BRICKS}.hive.metastore.schema.syncOnWrite", "true")
            .config(f"{_BRICKS}.delta.schema.autoMerge.enabled", "true")
            .config(f"{_BRICKS}.delta.schema.overwrite.mode", "true")
            .config(f"{_BRICKS}.delta.properties.defaults.columnMapping.mode", "name")
            .enableHiveSupport()
            .getOrCreate()
            )


_instance = _setup(_builder)
nds_instance = _instance
