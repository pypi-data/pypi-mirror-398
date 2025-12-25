import atexit
import logging
import os
import queue
import socket
import threading
import time
import typing
from pathlib import Path

from pydantic import BaseModel
from skywalking.trace.context import get_context

from linker_atom.config import settings


def build_current_date_str() -> str:
    return time.strftime('%Y%m%d')


def truncate_msg(msg: typing.Any):
    if isinstance(msg, dict):
        out_data = {}
        for key, value in msg.items():
            out_data[key] = truncate_msg(value)
        return out_data
    elif isinstance(msg, list):
        out_data = []
        for value in msg[:10]:
            out_data.append(truncate_msg(value))
        return out_data
    elif isinstance(msg, str):
        out_data = msg[:200]
        return out_data
    elif isinstance(msg, bytes):
        out_data = msg[:20]
        return out_data
    else:
        try:
            if hasattr(msg, '__dict__'):
                return truncate_msg(msg.__dict__)
        except:
            return msg
        return msg


class FileWriter:
    _lock = threading.RLock()
    
    def __init__(self, file_name: str, log_path: str, max_bytes: int, back_count: int):
        self._max_bytes = max_bytes
        self._back_count = back_count
        self.need_write_2_file = True if file_name else False
        if self.need_write_2_file:
            self._file_name = file_name
            self.log_path = log_path
            if not Path(self.log_path).exists():
                Path(self.log_path).mkdir(exist_ok=True)
            self._open_file()
            self._last_write_ts = 0
            self._last_del_old_files_ts = 0
    
    @property
    def file_path(self):
        log_list = [log_file for log_file in Path(self.log_path).glob(f'????????-????-{self._file_name}')]
        shard_log_list = [f.name.split('-')[1] for f in log_list if f'{build_current_date_str()}-' in f.name]
        
        if not shard_log_list:
            return Path(self.log_path) / Path(f'{build_current_date_str()}-0001-{self._file_name}')
        else:
            sn_max = max(shard_log_list)
            log_file_size = (Path(self.log_path) / Path(
                f'{build_current_date_str()}-{sn_max}-{self._file_name}')).stat().st_size
            if log_file_size > self._max_bytes:
                new_sn_int = int(sn_max) + 1
                new_sn_str = str(new_sn_int).zfill(4)
                return Path(self.log_path) / Path(f'{build_current_date_str()}-{new_sn_str}-{self._file_name}')
            else:
                return Path(self.log_path) / Path(f'{build_current_date_str()}-{sn_max}-{self._file_name}')
    
    def _open_file(self):
        self._f = open(self.file_path, encoding='utf8', mode='a')
    
    def _close_file(self):
        self._f.close()
    
    def write_2_file(self, msg):
        if self.need_write_2_file:
            with self._lock:
                now_ts = time.time()
                if now_ts - self._last_write_ts > 10:
                    self._last_write_ts = time.time()
                    self._close_file()
                    self._open_file()
                self._f.write(msg)
                self._f.flush()
                if now_ts - self._last_del_old_files_ts > 30:
                    self._last_del_old_files_ts = time.time()
                    self._delete_old_files()
    
    def _delete_old_files(self):
        log_list = [log_file for log_file in Path(self.log_path).glob(f'????????-????-{self._file_name}')]
        log_list.sort(key=lambda _f: _f.name, reverse=True)
        for f in log_list[self._back_count:]:
            try:
                f.unlink()
            except (FileNotFoundError, PermissionError):
                pass


class BulkFileWriter:
    _lock = threading.Lock()
    
    filename__queue_map = {}
    filename__options_map = {}
    filename__file_writer_map = {}
    
    _get_queue_lock = threading.Lock()
    
    _has_start_bulk_write = False
    
    @classmethod
    def _get_queue(cls, file_name):
        if file_name not in cls.filename__queue_map:
            cls.filename__queue_map[file_name] = queue.SimpleQueue()
        return cls.filename__queue_map[file_name]
    
    @classmethod
    def _get_file_writer(cls, file_name):
        if file_name not in cls.filename__file_writer_map:
            fw = FileWriter(**cls.filename__options_map[file_name])
            cls.filename__file_writer_map[file_name] = fw
        return cls.filename__file_writer_map[file_name]
    
    def __init__(
            self,
            file_name: typing.Optional[str],
            log_path: str,
            max_bytes: int,
            back_count: int
    ):
        self.need_write_2_file = True if file_name else False
        self._file_name = file_name
        if file_name:
            self.__class__.filename__options_map[file_name] = {
                'file_name': file_name,
                'log_path': log_path,
                'max_bytes': max_bytes,
                'back_count': back_count,
            }
            self.start_bulk_write()
    
    def write_2_file(self, msg):
        if self.need_write_2_file:
            with self._lock:
                self._get_queue(self._file_name).put(msg)
    
    @classmethod
    def _bulk_real_write(cls):
        with cls._lock:
            for _file_name, queue in cls.filename__queue_map.items():
                msg_str_all = ''
                while not queue.empty():
                    msg_str_all += queue.get()
                if msg_str_all:
                    cls._get_file_writer(_file_name).write_2_file(msg_str_all)
    
    @classmethod
    def when_exit(cls):
        return cls._bulk_real_write()
    
    @classmethod
    def start_bulk_write(cls):
        def _bulk_write():
            while 1:
                cls._bulk_real_write()
                time.sleep(0.1)
        
        if not cls._has_start_bulk_write:
            cls._has_start_bulk_write = True
            threading.Thread(target=_bulk_write, daemon=True).start()


atexit.register(BulkFileWriter.when_exit)

OsFileWriter = FileWriter if os.name == 'posix' else BulkFileWriter


class UdfStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.WARNING:
            record.msg = truncate_msg(record.msg)
        super().emit(record)


class BothDayAndSizeRotatingFileHandler(logging.Handler):
    
    def __init__(
            self,
            file_name: typing.Optional[str],
            log_path: str,
            max_bytes: int,
            back_count: int,
    ):
        super().__init__()
        self.os_file_writer = OsFileWriter(
            file_name=file_name,
            log_path=log_path,
            max_bytes=max_bytes,
            back_count=back_count
        )
    
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.WARNING:
            record.msg = truncate_msg(record.msg)
        msg = self.format(record)
        self.os_file_writer.write_2_file(f'{msg}\n')


class ContextFilter(logging.Filter):
    
    def filter(self, record):
        record.trace_id = self.trace_id
        return True
    
    @property
    def trace_id(self) -> str:
        context = get_context()
        trace_id = str(context.segment.related_traces[0])
        return trace_id


class UdfLogger(logging.Logger):
    
    def __init__(
            self,
            name,
            log_dir: str = 'logs',
            max_bytes: int = 100 << 10 << 10,
            back_count: int = 30,
            level=logging.NOTSET,
    ):
        super().__init__(name, level)
        self.init(log_dir, max_bytes, back_count)
    
    def init(
            self,
            log_dir: str = 'logs',
            max_bytes: int = 1 << 10 << 10,
            back_count: int = 30,
    ):
        hostname = socket.gethostname()
        logger_dir_path = os.path.join(log_dir, self.name, hostname)
        os.makedirs(logger_dir_path, exist_ok=True)
        formatter = logging.Formatter(
            '[%(trace_id)s|%(levelname)8s|%(asctime)s|%(pathname)s:%(lineno)d|%(funcName)s] %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        
        if not self.handlers:
            console_handler = UdfStreamHandler()
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)
            
            hostname = socket.gethostname()
            logger_dir_path = os.path.join(log_dir, self.name, hostname)
            os.makedirs(logger_dir_path, exist_ok=True)
            
            file_handler = BothDayAndSizeRotatingFileHandler(
                self.name + '.log',
                logger_dir_path,
                max_bytes=max_bytes,
                back_count=back_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(self.level)
            self.addHandler(file_handler)
            self.addFilter(ContextFilter())


logger = UdfLogger(
    name=settings.log_config.log_dir,
    max_bytes=settings.log_config.log_file_max_bytes,
    back_count=settings.log_config.log_backup_count,
)
