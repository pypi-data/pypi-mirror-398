from pydantic import BaseModel, Field


class MmapReadBody(BaseModel):
    path: str = Field(default='')
    position: int = Field(default=0)
    size: int = Field(default=0)
