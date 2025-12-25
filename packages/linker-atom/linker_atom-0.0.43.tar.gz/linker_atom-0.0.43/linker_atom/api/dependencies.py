from starlette.datastructures import State
from starlette.requests import Request


def get_state(request: Request) -> State:
    return request.app.state


def get_engine(request: Request):
    return get_state(request).engine
