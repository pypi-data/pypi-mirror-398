import asyncio
import time
import traceback
from collections import OrderedDict
from functools import wraps

from linker_atom.lib.log import logger


def record_duration(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        return_data = await func(*args, **kwargs)
        cost_time = round((time.perf_counter() - start_time) * 1000, 3)
        logger.debug(f'{func.__name__} duration: {cost_time}ms', stacklevel=2)
        return return_data

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        return_data = func(*args, **kwargs)
        cost_time = round((time.perf_counter() - start_time) * 1000, 3)
        logger.debug(f'{func.__name__} duration: {cost_time}ms', stacklevel=2)
        return return_data

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def catch_exc(calc_time: bool = False, default_data=None):
    def valid(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            return_data = default_data
            try:
                return_data = await func(*args, **kwargs)
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            if calc_time:
                cost_time = round(time.perf_counter() - start_time, 3)
                logger.debug(f'{func.__name__} duration: {cost_time}s', stacklevel=3)
            return return_data
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            return_data = default_data
            try:
                return_data = func(*args, **kwargs)
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            if calc_time:
                cost_time = round(time.perf_counter() - start_time, 3)
                logger.debug(f'{func.__name__} duration: {cost_time}s', stacklevel=3)
            return return_data
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return valid


@catch_exc()
def format_long_val(data):
    """
    长字符截断
    :param data:
    :return:
    """
    if isinstance(data, dict):
        out_data = {}
        for key, value in data.items():
            out_data[key] = format_long_val(value)
        return out_data
    if isinstance(data, list):
        out_data = []
        for value in data:
            out_data.append(format_long_val(value))
        return out_data
    if isinstance(data, str):
        out_data = data[:200]
        return out_data
    if isinstance(data, bytes):
        out_data = data[:20]
        return out_data
    return data


class LRUCache:
    # initialising capacity
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def has(self, key) -> bool:
        return key in self.cache
    
    def get(self, key):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def put(self, key, value) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def pop(self, key):
        self.cache.pop(key, None)
