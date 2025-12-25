from jupyterhub.apihandlers import default_handlers
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.scopes import needs_scope
from tornado import web

from .utils import EncryptJSONBody


class SpawnOptionsUpdateAPIHandler(EncryptJSONBody, APIHandler):
    @needs_scope("access:servers")
    async def post(self, user_name, server_name=""):
        user = self.find_user(user_name)
        if user is None:
            # no such user
            self.log.error(
                f"{user_name}:{server_name} - APICall: SpawnOptionsUpdate - No user found",
                extra={"user": user_name, "log_name": f"{user_name}:{server_name}"},
            )
            raise web.HTTPError(404)
        orm_user = user.orm_user

        formdata = await self.async_get_json_body()
        if server_name not in orm_user.orm_spawners:
            spawner = user.get_spawner(server_name, replace_failed=True)
            spawner.user_options = formdata
            spawner.orm_spawner.user_options = formdata
        else:
            spawner = orm_user.orm_spawners[server_name]
            spawner.user_options = formdata
        self.db.commit()
        self.set_status(204)


default_handlers.append(
    (r"/api/users/([^/]+)/server/update", SpawnOptionsUpdateAPIHandler)
)
default_handlers.append(
    (r"/api/users/([^/]+)/servers/([^/]*)/update", SpawnOptionsUpdateAPIHandler)
)
