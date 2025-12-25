import re
import time
from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
from pyinstrument import Profiler

from linker_atom.lib.common import catch_exc
from linker_atom.lib.log import logger

octet_stream_pattern = re.compile('application/octet-stream')
urlencoded_pattern = re.compile('application/x-www-form-urlencoded')
json_pattern = re.compile('application/json')
form_data_pattern = re.compile('multipart/form-data')
xml_pattern = re.compile(r'.*?/xml')
text_pattern = re.compile('text/plain')


@catch_exc()
async def handle_start(request: Request):
    headers_log = dict(
        _prefix='>>>Headers',
        headers=dict(request.headers.items()),
        host=request.client.host,
        method=request.method,
        path=request.url.path,
    )
    logger.debug(headers_log)
    
    params_log = dict(_prefix='>>>Params')
    if request.query_params:
        params_log['query_string'] = dict(request.query_params.items())
    
    body = await request.body()
    if body:
        content_type = request.headers.get("content-type")
        if re.match(json_pattern, content_type):
            params_log['json'] = await request.json()
        elif re.match(form_data_pattern, content_type):
            params_log['form_data'] = dict((await request.form()).items())
        elif re.match(urlencoded_pattern, content_type):
            params_log['urlencoded'] = dict((await request.form()).items())
        elif re.match(xml_pattern, content_type):
            params_log['xml'] = body.decode()
        elif re.match(text_pattern, content_type):
            params_log['plain'] = body.decode()
        else:
            params_log[content_type] = body
        logger.debug(params_log)


class ContextAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def handle_end(request: Request) -> Response:
            await handle_start(request)
            before = time.time()
            if request.app.state.settings.profiling or dict(request.query_params.items()).get('PROFILING'):
                profiler = Profiler()
                profiler.start()
                response: Response = await original_route_handler(request)
                profiler.stop()
                profiler.print()
                logger.warning(profiler.output_text())
            else:
                response: Response = await original_route_handler(request)
            duration = round((time.time() - before) * 1000, 3)
            headers_log = dict(
                _prefix='<<<Duration',
                host=request.client.host,
                method=request.method,
                path=request.url.path,
                duration=f'{duration}ms'
            )
            logger.debug(headers_log)
            return response
        
        return handle_end


class UdfAPIRoute(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, route_class=ContextAPIRoute, **kwargs)
