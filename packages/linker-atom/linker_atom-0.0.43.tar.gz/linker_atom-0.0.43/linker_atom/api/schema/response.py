from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from starlette import status


class BaseJsonResModel(BaseModel):
    code: int = Field(title='状态码')
    msg: str = Field(title='状态值说明')
    data: Optional[Union[Dict, str, List, Any]] = {}


class SuccessResponse(BaseJsonResModel):
    code: int = Field(default=0, title='状态码')
    msg: str = Field(default='Success', title='状态值说明')


class FailureResponse(BaseJsonResModel):
    code: int = Field(default=1, title='状态码')
    msg: str = Field(default='Failed', title='状态值说明')


class ExternalInvokeErrorResponse(FailureResponse):
    code: int = status.HTTP_400_BAD_REQUEST
    msg: str = 'External Invoke Error'


class RequestValidErrorResponse(FailureResponse):
    code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    msg: str = 'Request Entity Error'


class RequestNotFoundErrorResponse(FailureResponse):
    code: int = status.HTTP_404_NOT_FOUND
    msg: str = 'NOT FOUND'


class InternalErrorResponse(FailureResponse):
    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    msg: str = 'Internal Server Error'


class Heartbeat(BaseModel):
    is_alive: bool


class Object(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    conf: float
    label: str


class DetectionRes(BaseModel):
    code: int = 200
    msg: str = ''
    description: str = ''
    kwargs: dict = {}
    took: int
    objects: List[List[Object]] = []
