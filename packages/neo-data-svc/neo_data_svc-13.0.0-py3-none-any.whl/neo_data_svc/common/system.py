import base64
import datetime as dt
import hashlib
import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Union

import uvicorn

tz = 'Asia/Shanghai'
tz_info = timezone(timedelta(hours=8))


def run(app, host="0.0.0.0", port=8001):
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=1,
        access_log=True,
        server_header=False,
        headers=[("server", "NDP")],
    )


def autowire(file="push", pre="emdm.rest.ext.", f="process"):
    _m = pre + file.strip()
    m = importlib.import_module(_m)
    return getattr(m, f)


def F(filename):
    return Path(filename)


def get_now():
    return datetime.now(tz_info)


def time_str(now=None, fmt='%Y%m%d%H%M%S'):
    if not now:
        now = get_now()
    return now.strftime(fmt)


def T(now=None, fmt='%Y-%m-%d %H:%M:%S'):
    return time_str(now, fmt)


def Z():
    return T(datetime.min.replace(year=1900))


def get_today(now=None):
    if not now:
        now = get_now()
    return T(datetime(now.year, now.month, now.day, 0, 0, 0))


def timestamp_ms(now=None):
    if not now:
        now = get_now()
    return int(now.timestamp() * 1000)


def get_from(start="", full=False):
    return (start or (full and Z()) or get_today())


def digest(s, algorithm='MD5'):
    m = hashlib.new(algorithm)
    m.update(s.encode())
    return m.hexdigest()


def to_base64(s):
    return base64.b64encode(s.encode()).decode('ascii')


def load_json(s):
    return json.loads(s)
