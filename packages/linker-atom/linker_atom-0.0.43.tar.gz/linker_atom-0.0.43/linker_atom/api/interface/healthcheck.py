from linker_atom.api.base import UdfAPIRoute
from linker_atom.api.schema.response import Heartbeat
from linker_atom.config import settings

healthcheck_route = UdfAPIRoute()


@healthcheck_route.get(settings.healthcheck_url, response_model=Heartbeat, name="ping")
async def ping() -> Heartbeat:
    heartbeat = Heartbeat(is_alive=True)
    return heartbeat
