from jupyterhub.apihandlers import APIHandler
from jupyterhub.handlers import default_handlers
from jupyterhub.orm import Role


class DBHealthAPIHandler(APIHandler):
    async def get(self):
        Role.find(self.db, "any")
        self.set_status(200)


default_handlers.append((r"/api/health_db", DBHealthAPIHandler))
