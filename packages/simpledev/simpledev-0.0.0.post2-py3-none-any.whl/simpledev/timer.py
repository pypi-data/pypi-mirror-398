from time import time
from typing import Any


def delay(is_res: bool = False) -> Any:
    def decorator(func):
        def wrapper(*args, **kwargs):
            st = time()
            res = func(*args, **kwargs)
            if is_res:
                print(time() - st)
            return res if is_res else time() - st
        return wrapper
    return decorator
