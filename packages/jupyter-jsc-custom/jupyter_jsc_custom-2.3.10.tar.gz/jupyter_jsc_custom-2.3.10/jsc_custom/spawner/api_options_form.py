#
#
# This endpoint is used by the Slurm Provisioner Extension.
#
#
import json

from jupyterhub.apihandlers import default_handlers
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.scopes import needs_scope
from tornado import web

from ..authenticator.oauthenticator import res_pattern
from ..misc import get_custom_config
from ..misc import get_reservations


def get_dropdown_lists(entitlements, system_, account_):
    custom_config = get_custom_config()
    reservations_all = get_reservations()
    projects_ret = []
    partitions_ret = {}
    reservations_ret = {}

    for entry in entitlements:
        match = res_pattern.match(entry)
        if match:
            # namespace = match.group("namespace")
            systempartition = match.group("systempartition")
            if systempartition:
                systempartition = systempartition.lower()
            project = match.group("project")
            account = match.group("account")
            # accounttype = match.group("accounttype")
            system = custom_config.get("mapSystems", {}).get(systempartition, None)
            partition = custom_config.get("mapPartitions", {}).get(
                systempartition, None
            )
            if not system or system != system_ or account != account_:
                continue
            if project not in projects_ret:
                projects_ret.append(project)
            interactive_partitions = (
                custom_config.get("systems", {})
                .get(system, {})
                .get("interactivePartitions", [])
            )
            if partition and partition not in interactive_partitions:
                if project not in partitions_ret.keys():
                    partitions_ret[project] = []
                if partition not in partitions_ret[project]:
                    partitions_ret[project].append(partition)
                    for default_partition in custom_config.get(
                        "defaultPartitions", {}
                    ).get(systempartition, []):
                        default_partition = custom_config.get("mapPartitions", {}).get(
                            default_partition, None
                        )
                        if (
                            default_partition
                            and default_partition not in partitions_ret[project]
                        ):
                            partitions_ret[project].append(default_partition)

    for project, partitions_ in partitions_ret.items():
        for partition in partitions_:
            if project not in reservations_ret.keys():
                reservations_ret[project] = {}
            if partition not in reservations_ret[project].keys():
                reservations_ret[project][partition] = ["None"] + [
                    x.get("ReservationName")
                    for x in reservations_all.get(system, [])
                    if (
                        account in x.get("Users", "")
                        or project in x.get("Accounts", "")
                    )
                    and x.get("PartitionName", "(null)") in ["", "(null)", partition]
                    and x.get("State", "INACTIVE") == "ACTIVE"
                ]

    resources = custom_config.get("resources", {}).get(system_, {})
    return {
        "dropdown_lists": {
            "projects": projects_ret,
            "partitions": partitions_ret,
            "reservations": reservations_ret,
        },
        "resources": resources,
    }


class SpawnOptionsFormAPIHandler(APIHandler):
    @needs_scope("access:servers")
    async def get(self, user_name, server_name=""):
        user = self.find_user(user_name)
        if user is None:
            # no such user
            self.log.error(
                f"{user_name}:{server_name} - APICall: SpawnOptionsUpdate - No user found",
                extra={"user": user_name, "log_name": f"{user_name}:{server_name}"},
            )
            raise web.HTTPError(404)
        orm_user = user.orm_user

        if server_name not in orm_user.orm_spawners:
            # user has no such server
            self.log.error(
                f"{user_name}:{server_name} - APICall: SpawnOptionsUpdate - No spawner found",
                extra={
                    "user": user,
                    "spawner": server_name,
                    "log_name": f"{user_name}:{server_name}",
                },
            )
            raise web.HTTPError(404)

        auth_state = await user.get_auth_state()

        # Collect information from Spawner object
        spawner = user.spawners[server_name]
        system = spawner.user_options.get("system")
        account = spawner.user_options.get("hpc", {}).get("account")

        entitlements = auth_state.get("oauth_user", {}).get("entitlements")

        ret = get_dropdown_lists(entitlements, system, account)
        self.write(json.dumps(ret))


default_handlers.append(
    (r"/api/users/([^/]+)/server/optionsform", SpawnOptionsFormAPIHandler)
)
default_handlers.append(
    (r"/api/users/([^/]+)/servers/([^/]+)/optionsform", SpawnOptionsFormAPIHandler)
)
