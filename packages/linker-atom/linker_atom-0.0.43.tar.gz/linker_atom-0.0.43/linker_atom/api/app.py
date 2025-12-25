from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware

from linker_atom.api.middleware.event import register_app_middleware
from linker_atom.api.middleware.http import http_middleware
from linker_atom.api.route import api_router
from linker_atom.config import Settings, settings


def get_app(config=None):
    if config is None:
        config = settings
    else:
        config = Settings.parse_obj(config)
        
    app_config = dict(
        title=config.atom_title,
        description=config.atom_description,
        default_response_class=ORJSONResponse,
    )
    if not config.docs_switch:
        app_config['docs_url'] = None
        app_config['redoc_url'] = None

    app = FastAPI(
        **app_config
    )
    
    # 注册中间件
    register_app_middleware(app, config)
    app.middleware("http")(http_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # 注册路由
    app.include_router(
        router=api_router(),
    )
    return app
