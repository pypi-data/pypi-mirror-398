import time
from functools import wraps

from utils.logger import get_logger

logger = get_logger(__name__)


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        t1 = time.perf_counter()
        logger.info(f"{func.__name__} 执行时间: {t1 - t0:.3f} 秒")
        return res

    return wrapper
