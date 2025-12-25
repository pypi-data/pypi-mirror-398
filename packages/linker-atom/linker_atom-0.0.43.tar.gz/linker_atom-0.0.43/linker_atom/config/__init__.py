import os
from typing import List

from pydantic import BaseModel, Field

from linker_atom.config.logger import LoggerConfig
from linker_atom.config.serving import ServingConfig
from linker_atom.config.skywalking import SkyWalkingConfig


class Settings(BaseModel):
    atom_workers: int = Field(default=int(os.getenv('ATOM_WORKERS', 1)))
    atom_port: int = Field(default=int(os.getenv('ATOM_PORT', 8000)))
    atom_inner_start_port: int = Field(default=int(os.getenv('ATOM_INNER_START_PORT', 9000)))
    atom_title: str = Field(default=os.getenv('ATOM_TITLE', 'Atom'))
    atom_description: str = Field(default=os.getenv('ATOM_DESC', 'Atom'))
    atom_api_prefix: str = Field(default=os.getenv('ATOM_API_PREFIX', ''))
    
    log_config: LoggerConfig = Field(default=LoggerConfig())
    sw_config: SkyWalkingConfig = Field(default=SkyWalkingConfig())
    
    serving_meta_raw: str = Field(default=os.getenv('META', ""))
    docs_switch: bool = Field(default=bool(os.getenv('DOCS_SWITCH', True)))
    profiling: bool = Field(default=bool(os.getenv('PROFILING', False)))
    
    @property
    def model_id_list(self) -> List[str]:
        return list(filter(None, self.serving_config.model_ids.split(",")))
    
    @property
    def serving_config(self):
        if self.serving_meta_raw:
            return ServingConfig.parse_raw(self.serving_meta_raw)
        return ServingConfig()
    
    @property
    def healthcheck_url(self) -> str:
        if not self.serving_meta_raw:
            return self.atom_api_prefix + self.serving_config.atom_healthcheck_url
        if not self.serving_config.atom_healthcheck_url:
            return self.atom_api_prefix + '/v1/health/ping'
        return self.serving_config.atom_healthcheck_url


settings = Settings()
