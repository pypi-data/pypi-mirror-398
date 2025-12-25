import traceback
from typing import Callable

from fastapi.responses import ORJSONResponse
from starlette.requests import Request
from starlette.responses import Response

from linker_atom.api.schema.response import InternalErrorResponse
from linker_atom.lib.log import logger


async def http_middleware(request: Request, call_next: Callable) -> Response:
    """
    http请求接收/返回中间件
    捕获接口异常处理
    :param request:
    :param call_next:
    :return:
    """
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(traceback.format_exc())
        model = InternalErrorResponse(msg=str(e))
        response = ORJSONResponse(
            content=model.dict(),
            status_code=model.code
        )
    finally:
        pass
    return response
