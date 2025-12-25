import os
import uuid

from pydantic import BaseModel, Field


class SkyWalkingConfig(BaseModel):
    sw_switch: bool = Field(default=bool(os.getenv('SW_SWITCH', False)))
    sw_agent_backend: str = Field(default=os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES', ""))
    sw_agent_name: str = Field(default=os.getenv('SW_AGENT_NAME', ""))
    sw_agent_instance_name: str = Field(default=os.getenv('SW_AGENT_INSTANCE_NAME', uuid.uuid4().hex))
    sw_agent_log_reporter_active: bool = Field(default=bool(os.getenv('SW_AGENT_LOG_REPORTER_ACTIVE', True)))
    sw_agent_log_reporter_level: str = Field(default=os.getenv('SW_AGENT_LOG_REPORTER_LEVEL', "DEBUG"))
