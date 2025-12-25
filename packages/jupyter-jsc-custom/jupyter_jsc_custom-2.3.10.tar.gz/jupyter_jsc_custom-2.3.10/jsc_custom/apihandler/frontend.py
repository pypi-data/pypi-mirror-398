import json

from jupyterhub.handlers import default_handlers
from tornado import web

from ..misc import get_custom_config
from ..misc import get_incidents
from ..misc import get_reservations
from ..spawner import jhub_hostname
from ..spawner.utils import async_decrypted_user_options
from .misc import NoXSRFCheckAPIHandler


class FHostnameAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        self.write(jhub_hostname.encode())
        self.set_status(200)
        return


class FSystemConfigAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        self.write(json.dumps(get_custom_config().get("systems", {})))
        self.set_status(200)
        return


class FMapSystemsAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("mapSystems", {})))
        self.set_status(200)
        return


class FMapPartitionsAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("mapPartitions", {})))
        self.set_status(200)
        return


class FDefaultPartitionsAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("defaultPartitions", {})))
        self.set_status(200)
        return


class FServicesAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("services", {})))
        self.set_status(200)
        return


class FResourcesAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("resources", {})))
        self.set_status(200)
        return


class FUserModulesAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("userModules", {})))
        self.set_status(200)
        return


class FBackendServicesAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_custom_config().get("backendServices", {})))
        self.set_status(200)
        return


class FIncidentCheckAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        self.write(json.dumps(get_incidents(user)))
        self.set_status(200)
        return


class FReservationsAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            self.write(json.dumps(get_reservations()))
        self.set_status(200)
        return


class FUserOptionsAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is not None:
            user_options = await async_decrypted_user_options(user)
            if "" in user_options.keys():
                del user_options[""]
            self.write(json.dumps(user_options))
        self.set_status(200)
        return


class FUserAPIHandler(NoXSRFCheckAPIHandler):
    async def get(self):
        self.set_header("Cache-Control", "no-cache")
        user = self.current_user
        if user is None:
            raise web.HTTPError(404)

        ret = {}
        custom_config = get_custom_config()
        ret["mapSystems"] = (custom_config.get("mapSystems", {}),)
        ret["mapPartitions"] = (custom_config.get("mapPartitions", {}),)
        ret["defaultPartitions"] = (custom_config.get("defaultPartitions", {}),)
        ret["serviceConfig"] = (custom_config.get("services", {}),)
        ret["userModules"] = (custom_config.get("userModules", {}),)
        ret["resourcesConfig"] = (custom_config.get("resources", {}),)
        ret["backendServices"] = (custom_config.get("backendServices", {}),)
        ret["incidents"] = get_incidents(user)
        ret["reservations"] = (get_reservations(),)
        user_options = await async_decrypted_user_options(user)
        if "" in user_options.keys():
            del user_options[""]
        ret["decrypted_user_options"] = user_options
        self.write(json.dumps(ret))
        self.set_status(200)
        return


default_handlers.append((r"/api/f/hostname", FHostnameAPIHandler))
default_handlers.append((r"/api/f/systemconfig", FSystemConfigAPIHandler))
default_handlers.append((r"/api/f/mapsystems", FMapSystemsAPIHandler))
default_handlers.append((r"/api/f/mappartitions", FMapPartitionsAPIHandler))
default_handlers.append((r"/api/f/defaultpartitions", FDefaultPartitionsAPIHandler))
default_handlers.append((r"/api/f/services", FServicesAPIHandler))
default_handlers.append((r"/api/f/resources", FResourcesAPIHandler))
default_handlers.append((r"/api/f/usermodules", FUserModulesAPIHandler))
default_handlers.append((r"/api/f/backendservices", FBackendServicesAPIHandler))
default_handlers.append((r"/api/f/incidents", FIncidentCheckAPIHandler))
default_handlers.append((r"/api/f/reservations", FReservationsAPIHandler))
default_handlers.append((r"/api/f/useroptions", FUserOptionsAPIHandler))

default_handlers.append((r"/api/f/users", FUserAPIHandler))
