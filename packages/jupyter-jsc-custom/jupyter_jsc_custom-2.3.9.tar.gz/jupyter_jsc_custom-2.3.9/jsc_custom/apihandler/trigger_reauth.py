from forwardbasespawner.utils import check_custom_scopes
from jupyterhub.apihandlers import APIHandler
from jupyterhub.apihandlers import default_handlers
from tornado import web


class ReauthenticatorAPIHandler(APIHandler):
    required_scopes = ["custom:reauthenticate:set"]

    async def post(self, user_name):
        check_custom_scopes(self)
        user = self.find_user(user_name)
        if user is None:
            raise web.HTTPError(404)
        auth_state = await user.get_auth_state()
        auth_state["reauthenticate"] = True
        await user.save_auth_state(auth_state)
        self.set_status(204)


default_handlers.append((r"/api/reauthenticate/([^/]+)", ReauthenticatorAPIHandler))
