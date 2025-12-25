import hashlib
import json
import random
import string
import urllib.parse
from datetime import datetime

from jupyterhub.handlers import default_handlers
from jupyterhub.handlers.pages import SpawnHandler
from jupyterhub.utils import url_path_join
from tornado import web

from ..misc import get_custom_config
from ..orm.share import UserOptionsShares


def generate_random_id():
    chars = string.ascii_lowercase
    all_chars = string.ascii_lowercase + string.digits

    # Start with a random lowercase letter
    result = random.choice(chars)

    # Add 31 more characters from lowercase letters and numbers
    result += "".join(random.choice(all_chars) for _ in range(31))

    return result


class ShareUserOptionsSpawnHandler(SpawnHandler):
    async def _render_form(self, for_user, server_name):
        auth_state = await for_user.get_auth_state()
        return await self.render_template(
            "home.html", for_user=for_user, auth_state=auth_state, row=server_name
        )

    def upgrade_user_options(self, user_options):
        # In the past we had a different structure for our share user options
        # To support old share links, we have to upgrade them to the newest structure
        if user_options.get("profile", "").startswith("JupyterLab/"):
            name = user_options.get("name", "Unnamed")
            option_dict = {
                "JupyterLab/repo2docker": "repo2docker",
                "JupyterLab/custom": "custom",
            }
            profile = option = option_dict.get(user_options.get("profile", ""))
            service = "jupyterlab"
            secret_keys = []
            system = user_options.get("system", "unknown")
            flavor = user_options.get("flavor", None)
            r2dnotebooktype = user_options.get("notebook_type", "file")
            r2drepo = user_options.get("repo", None)
            if r2drepo and r2drepo.startswith("https://github.com/"):
                r2dtype = "gh"
                r2drepo = r2drepo[len("https://github.com/") :]
            else:
                r2dtype = "git"
            r2dgitref = user_options.get("gitref", "")
            r2dnotebook = user_options.get("notebook", None)
            ret = {
                "name": name,
                "service": service,
                "option": option,
                "profile": profile,
                "system": system,
                "secrets": secret_keys,
            }
            if flavor:
                ret["flavor"] = flavor
            if r2drepo:
                ret["repo2docker"] = {
                    "repotype": r2dtype,
                    "repourl": r2drepo,
                    "reporef": r2dgitref,
                }
                if r2dnotebook:
                    ret["repo2docker"]["repopath"] = r2dnotebook
                    ret["repo2docker"]["repopathtype"] = r2dnotebooktype

            image = user_options.get("image", None)
            if image:
                ret["custom"] = {"customimage": image}
            userdata_path = user_options.get("userdata_path", None)
            if userdata_path:
                ret["storage"] = {"localstoragepath": userdata_path}
            return True, ret
        else:
            return False, user_options

    @web.authenticated
    async def get(self, secret):
        user = self.current_user
        db_entry = UserOptionsShares.find_by_share_id(self.db, secret)
        if not db_entry:
            raise web.HTTPError(400, f"Unknown share id: {secret}")

        server_name = None
        for key, orm_spawner in user.orm_user.orm_spawners.items():
            if (
                orm_spawner.user_options
                and orm_spawner.user_options.get("share_id", "") == db_entry.share_id
            ):
                server_name = key
                break

        if not server_name:
            server_name = generate_random_id()

        spawner = user.get_spawner(server_name, replace_failed=True)
        upgrade, user_options = self.upgrade_user_options(db_entry.user_options)
        db_entry.last_used = datetime.now()
        if upgrade:
            db_entry.user_options = user_options
        self.db.add(db_entry)
        self.db.commit()
        spawner.user_options = user_options
        spawner.user_options["share_id"] = secret
        spawner.orm_spawner.user_options = db_entry.user_options
        self.db.add(spawner.orm_spawner)
        self.db.commit()

        url = url_path_join(self.hub.base_url, "start", user.name, spawner.name)
        self.redirect(url)


class R2DHandler(SpawnHandler):
    async def arguments_to_user_options(
        self, user, repotype_, args, arguments_dict_lower
    ):
        user_options = {"repo2docker": {}}

        repotype = urllib.parse.unquote(repotype_)

        if repotype in ["gh", "gist", "git", "gl"]:
            ref = urllib.parse.unquote(args[-1])
            args = args[:-1]
            user_options["repo2docker"]["reporef"] = ref

        user_options["service"] = "jupyterlab"
        user_options["option"] = "repo2docker"

        args_unquote = [urllib.parse.unquote(x) for x in args]
        user_options["repo2docker"]["repotype"] = repotype
        user_options["repo2docker"]["repourl"] = "/".join(args_unquote)

        if len(arguments_dict_lower.get("name", [])) > 0:
            user_options["name"] = arguments_dict_lower.get("name")[0].decode("utf-8")
        else:
            if repotype == "gh":
                user_options["name"] = args_unquote[0]
            else:
                user_options["name"] = user_options["repo2docker"]["repourl"]

        # if "labpath" in self.request.arguments
        if len(arguments_dict_lower.get("labpath", [])) > 0:
            user_options["repo2docker"]["repopathtype"] = "file"
            user_options["repo2docker"]["repopath"] = arguments_dict_lower.get(
                "labpath"
            )[0].decode("utf-8")
        elif len(arguments_dict_lower.get("urlpath", [])) > 0:
            user_options["repo2docker"]["repopathtype"] = "url"
            user_options["repo2docker"]["repopath"] = arguments_dict_lower.get(
                "urlpath"
            )[0].decode("utf-8")

        # Get System
        auth_state = await user.get_auth_state()
        if len(arguments_dict_lower.get("system", [])) > 0:
            system = arguments_dict_lower.get("system")[0].decode("utf-8")
        elif len(auth_state.get("outpost_flavors", {}).keys()) > 0:
            try:
                custom_config = get_custom_config()
                if (
                    "deNBI-Cloud" in custom_config.get("systems", {}).keys()
                    and "deNBI-Cloud" in auth_state.get("outpost_flavors", {}).keys()
                ):
                    system = "deNBI-Cloud"
                else:
                    system = list(auth_state.get("outpost_flavors", {}).keys())[0]
            except:
                self.log.exception("Could not check for systems")
                system = "JSC-Cloud"
        else:
            system = "JSC-Cloud"
        user_options["system"] = system

        # Get Flavor
        if len(arguments_dict_lower.get("flavor", [])) > 0:
            flavor = arguments_dict_lower.get("flavor")[0].decode("utf-8")
        else:
            flavors = auth_state.get("outpost_flavors", {}).get(system, {})
            flavor = max(
                flavors,
                key=lambda k: flavors.get(k, {}).get("weight", -1),
                default="_undefined",
            )

        user_options["flavor"] = flavor

        # Check if persistent storage is required
        if len(arguments_dict_lower.get("localstoragepath", [])) > 0:
            user_options["storage"] = {
                "localstoragepath": arguments_dict_lower.get("localstoragepath")[
                    0
                ].decode("utf-8")
            }
        elif "localstoragepath" in arguments_dict_lower.keys():
            user_options["storage"] = {"localstoragepath": "/home/jovyan/work"}

        return user_options

    @web.authenticated
    async def get(self, repotype_, args):
        args = args.split("/")
        user = self.current_user
        arguments_dict_bytes = self.request.query_arguments
        arguments_dict_lower = {k.lower(): v for k, v in arguments_dict_bytes.items()}
        user_options = await self.arguments_to_user_options(
            user, repotype_, args, arguments_dict_lower
        )
        hash_str_full = json.dumps(user_options, sort_keys=True) + user.name
        hash_str = hashlib.sha256(hash_str_full.encode()).hexdigest()
        user_options["r2d_id"] = hash_str

        server_name = None
        for key, orm_spawner in user.orm_user.orm_spawners.items():
            if (
                orm_spawner.user_options
                and orm_spawner.user_options.get("r2d_id", "") == hash_str
            ):
                server_name = key
                break

        if not server_name:
            server_name = generate_random_id()

        spawner = user.get_spawner(server_name, replace_failed=True)
        spawner.user_options = user_options
        spawner.orm_spawner.user_options = user_options
        self.db.add(spawner.orm_spawner)
        self.db.commit()

        url = url_path_join(self.hub.base_url, "start", user.name, spawner.name)
        self.redirect(url)


default_handlers.append((r"/share/user_options/([^/]+)", ShareUserOptionsSpawnHandler))
default_handlers.append((r"/share/([^/]+)", ShareUserOptionsSpawnHandler))
default_handlers.append((r"/r2d/([^/]+)/(.*)", R2DHandler))
default_handlers.append((r"/v2/([^/]+)/(.*)", R2DHandler))
