import logging
from functools import wraps


def nds_log(f):
    @wraps(f)
    def _deco(*args, **kwargs):
        logger = logging.getLogger(f.__module__)
        logger.debug(f"{f.__name__} => {args}, {kwargs}")

        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f"{f.__name__} => {e}")
            raise
    return _deco
