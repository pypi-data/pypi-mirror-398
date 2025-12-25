from linker_atom.api.base import UdfAPIRoute
from linker_atom.api.interface.healthcheck import healthcheck_route


def api_router():
    router = UdfAPIRoute()
    router.include_router(healthcheck_route)
    
    return router
