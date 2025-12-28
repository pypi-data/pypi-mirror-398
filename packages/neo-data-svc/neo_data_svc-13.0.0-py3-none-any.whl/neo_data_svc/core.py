import logging
import re

from .rdms import ProjectQuery, ProjectWhere
from .repo import *

logger = logging.getLogger(__name__)


@nds_extern_call
def nds_query_table(table, fields="*", body=None):
    if not body:
        body = {}

    q = ProjectQuery(
        table=table,
        fields=fields,
        where=ProjectWhere.model_validate(body))

    page_no = q.where.pageNo
    page_size = q.where.pageSize
    sqlwhere = (q.where.sqlwhere or "").strip()
    start = (page_no - 1) * page_size + 1
    end = page_no * page_size
    logger.debug(f"📤 [{table}] [{start}->{end}] [{sqlwhere}]")
    return nds_query(table, fields, start, end, sqlwhere)


@nds_extern_call
def nds_refresh_table(table, data, keys):
    if not data or not keys:
        return

    if not isinstance(keys, (list, tuple)):
        keys = [keys]

    logger.debug(f"📥 [{table}] -> {keys}")
    nds_refresh(table, data, keys)
