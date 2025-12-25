import mmap
import time
from collections import OrderedDict
from typing import Any, Dict

from pydantic import BaseModel


class FileManager(BaseModel):
    connect_time: float
    fn: Any


class CacheManager:
    
    def __init__(self, period=60) -> None:
        self.period = period
        self.cache: Dict[Any, FileManager] = OrderedDict()
    
    def set(self, name, value: mmap.mmap):
        self.expire()
        self.cache[name] = FileManager(
            connect_time=time.time(),
            fn=value
        )
    
    def get(self, name, default=None):
        self.expire()
        if name not in self.cache:
            return default
        return self.cache[name].fn if self.cache.get(name, default) else default
    
    def expire(self):
        expired_key = list(filter(lambda x: (time.time() - self.cache[x].connect_time) > self.period, self.cache))
        list(map(self.cache.pop, expired_key))
        return


class MmapManager:
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(MmapManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, path: str, length=0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, period=60 * 10) -> None:
        self.path = path
        self.length = length
        self.flags = flags
        self.prot = prot
    
    def read(self, position: int, size: int) -> bytes:
        with open(self.path, 'rb') as f:
            mm = mmap.mmap(
                f.fileno(),
                length=self.length,
                flags=self.flags,
                prot=self.prot,
            )
            mm.seek(position)
            buffer = mm.read(size)
            mm.close()
        return buffer
