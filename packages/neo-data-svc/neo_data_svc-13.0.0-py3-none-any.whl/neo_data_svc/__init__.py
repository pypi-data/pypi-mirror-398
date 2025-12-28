
from contextlib import asynccontextmanager

import typer
from fastapi import Body, Depends, FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from .cache import nds_cache, nds_cache_init
from .core import *
from .rdms import *


async def ndp_make_ep(r, body, ep, db, cls, token):
    obj = await ndp_get(db, cls, ep=ep)
    if not obj:
        raise RuntimeError(f"💥 No {ep}")

    table = obj.table.strip()
    func = obj.func

    if not obj.enable:
        raise RuntimeError(f"💥 No active {ep}")

    if func:
        ndp_sys.autowire(func)(body, table, r)
        return PushOut()

    if not table:
        raise RuntimeError("💥 Need table")

    result = nds_query_table(table, obj.fields, body)
    return QueryOut(data=InnerData(result=result))

app = typer.Typer()
ndp_cmd = app.command
