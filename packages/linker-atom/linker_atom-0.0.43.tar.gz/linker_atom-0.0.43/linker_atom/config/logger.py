import os
from pydantic import BaseModel, Field


class LoggerConfig(BaseModel):
    log_backup_count: int = Field(default=int(os.getenv('LOG_BACKUP_COUNT', 30)))
    log_dir: str = Field(default=os.getenv('LOG_DIR', "atom"))
    log_file_max_bytes: int = Field(default=int(os.getenv('LOG_FILE_MAX_BYTES', 100 << 10 << 10)))
