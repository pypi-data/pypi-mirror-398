import os
import socket
import time

import requests
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from skywalking import agent
from skywalking import config
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import Route

from linker_atom.api.schema.response import FailureResponse, RequestValidErrorResponse
from linker_atom.config import ServingConfig, Settings, SkyWalkingConfig
from linker_atom.lib.log import logger
from linker_atom.lib.requests import get, post


def heartbeat(app):
    serving_config: ServingConfig = app.state.settings.serving_config
    hostname = socket.gethostname()
    url = serving_config.serving_domain + "/atom/health"
    json_body = {
        "atomInstanceName": hostname,
    }
    try:
        response = requests.post(url, json=json_body, timeout=15)
        response = response.json()
        if response.get("code") == "0":
            if response.get("data", "") == "register":
                register_service_info(app)
            return
    except Exception as e:
        logger.warning(e)
        logger.warning("register heartbeat info failed")


def startup_skywalking(app: FastAPI):
    sw_config: SkyWalkingConfig = app.state.settings.sw_config
    if sw_config.sw_switch:
        sw_agent = agent
        config.init(
            agent_collector_backend_services=sw_config.sw_agent_backend,
            agent_name=sw_config.sw_agent_name,
            agent_instance_name=sw_config.sw_agent_instance_name,
            agent_log_reporter_active=sw_config.sw_agent_log_reporter_active,
            agent_log_reporter_level=sw_config.sw_agent_log_reporter_level,
        )
        sw_agent.start()
        logger.debug("skywalking running...")
        return sw_agent


def background_register_info_heartbeat(app: FastAPI):
    settings: Settings = app.state.settings
    background: BackgroundScheduler = app.state.schedulers
    serve_ping_uri = f"http://localhost:{settings.atom_port}{settings.healthcheck_url}"
    
    while 1:
        response = get(serve_ping_uri, timeout=15)
        if response.status_code == 200:
            register_service_info(app)
            background.add_job(
                func=heartbeat,
                args=(app,),
                trigger=IntervalTrigger(seconds=2),
                coalesce=True,
                misfire_grace_time=30 * 1,
                max_instances=1,
                id="register_heartbeat",
            )
            background.remove_job("register_info_heartbeat")
            return
        time.sleep(2)


def register_service_info(app: FastAPI):
    settings: Settings = app.state.settings
    serving_config: ServingConfig = settings.serving_config
    hostname = socket.gethostname()
    url = serving_config.serving_domain + "/atom/register"
    json_body = {
        "abilityCode": serving_config.ability_code,
        "abilityCodeInstance": serving_config.ability_code_instance,
        "abilityDependAtomCodes": serving_config.ability_depend_atom_codes,
        "atomCode": serving_config.atom_code,
        "atomInstanceName": hostname,
        "requestUrl": serving_config.atom_uri,
    }
    while 1:
        try:
            response = post(url, json=json_body, timeout=15)
            response = response.json()
            if response.get("code") == "0":
                logger.debug("register service info successful")
                return
            else:
                logger.warning("register service info failed, will retry after 2s")
                time.sleep(2)
        except Exception as e:
            logger.warning(e)
            logger.warning("register service info failed, will retry after 2s")
            time.sleep(2)


def startup_schedulers(app: FastAPI):
    schedulers = BackgroundScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=os.cpu_count())},
        job_defaults={
            "coalesce": False,
            "misfire_grace_time": 60 * 60 * 2,
            "max_instances": 5,
        },
    )
    schedulers.start()
    logger.debug("schedulers running...")
    return schedulers


def shutdown_deregister_service_info(app: FastAPI):
    serving_config: ServingConfig = app.state.settings.serving_config
    hostname = socket.gethostname()
    url = serving_config.serving_domain + "/atom/unRegister"
    json_body = {
        "atomInstanceName": hostname,
    }
    try:
        response = post(url, json=json_body, timeout=15)
        response = response.json()
        if response.get("code") == "0":
            logger.debug("deregister service info successful")
            return
    except Exception as e:
        logger.warning(e)
        logger.warning("deregister service info failed")


def register_app_middleware(app, settings):
    @app.on_event("startup")
    async def startup_event():
        log_dict = dict(
            _prefix='>>>Running Config',
            config=settings.dict(),
        )
        logger.debug(log_dict)
        app.state.settings = settings
        app.state.sw_agent = startup_skywalking(app)
        app.state.schedulers = startup_schedulers(app)
        
        if settings.serving_meta_raw and settings.serving_config.serving_host:
            app.state.schedulers.add_job(
                func=background_register_info_heartbeat,
                args=(app,),
                trigger=IntervalTrigger(seconds=2),
                coalesce=True,
                misfire_grace_time=60 * 1,
                max_instances=1,
                id="register_info_heartbeat",
            )
        
        route: Route
        for route in app.routes:
            logger.debug(f"{route.methods} {route.path}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        settings = app.state.settings
        try:
            app.state.schedulers.shutdown()
            sw_config = app.state.settings.sw_config
            if sw_config.sw_switch:
                app.state.sw_agent.stop()
            
            if settings.serving_meta_raw and settings.serving_config.serving_host:
                shutdown_deregister_service_info(app)
        except Exception as e:
            logger.warning(e)
            pass
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
            request: Request, exc: RequestValidationError
    ):
        model = RequestValidErrorResponse(data=exc.errors())
        response = ORJSONResponse(content=model.dict(), status_code=model.code)
        logger.warning(
            f"<<<{request.client.host}|{request.method}|{request.url.path}|{response.status_code}\n"
        )
        return response
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        model = FailureResponse(code=exc.status_code, msg=exc.detail)
        response = ORJSONResponse(content=model.dict(), status_code=model.code)
        logger.warning(
            f"<<<{request.client.host}|{request.method}|{request.url.path}|{exc.status_code}\n"
        )
        return response
    
    return app
