import json

from jupyterhub.handlers import default_handlers

from ..misc import get_incidents
from .misc import NoXSRFCheckAPIHandler


class IncidentsAPIHandler(NoXSRFCheckAPIHandler):
    """
    This endpoint is used to show the current incidents.
    """

    async def get(self):
        self.write(json.dumps(get_incidents()))
        self.set_status(200)
        return


default_handlers.append((r"/api/incidents", IncidentsAPIHandler))
