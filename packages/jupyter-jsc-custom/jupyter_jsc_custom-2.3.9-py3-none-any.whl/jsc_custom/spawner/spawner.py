import asyncio
import copy
import json
import os
import random
import re
import time
from datetime import datetime

from datefinder import find_dates
from outpostspawner import OutpostSpawner
from sqlalchemy import inspect
from tornado.httpclient import HTTPRequest
from unicorespawner import UnicoreSpawner

from ..apihandler.user_count import get_user_count
from ..misc import get_custom_config
from ..misc import get_global_sse
from ..misc import get_incidents
from .utils import recursive_decrypt


class CustomJSCSpawner(OutpostSpawner, UnicoreSpawner):
    pass


async def extra_labels(spawner, user_options):
    labels = {
        "hub.jupyter.org/username": re.sub(
            r"[^a-zA-Z0-9\_\.\-]", "-", str(spawner.user.name)
        ),
        "hub.jupyter.org/servername": re.sub(
            r"[^a-zA-Z0-9\_\.\-]", "-", str(spawner.name)
        ),
        "component": "singleuser-server",
        "app": re.sub(
            r"[^a-zA-Z0-9\_\.\-]",
            "-",
            str(os.environ.get("JUPYTERHUB_APP", "jupyterhub")),
        ),
    }
    skip_options = ["name", "modules", "userdata_path", "repo2dockerdirectlink"]
    skip_options.extend(user_options.get("secret_keys", []))
    for param, value in spawner.user_options.items():
        if param in skip_options:
            continue
        param = param.replace("@", "_at_")
        param = re.sub(r"[^a-zA-Z0-9\_\.\-]", "-", str(param))  # remove forbidden chars
        key = f"hub.jupyter.org/{param}"
        value = re.sub(r"[^a-zA-Z0-9\_\.\-]", "-", str(value))  # remove forbidden chars
        # check if value is allowed
        label_is_allowed = bool(
            re.fullmatch(r"([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]", value)
        )
        if not label_is_allowed:
            # try to append a char
            valuez = f"{value}z"
            label_is_allowed = bool(
                re.fullmatch(r"([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]", valuez)
            )
            if not label_is_allowed:
                spawner.log.info(
                    f"{spawner._log_name} - Label {value} is not allowed. Skip it"
                )
                continue
            value = valuez
        labels.update({key: value})
    for key, value in labels.items():
        if len(value) > 63:
            labels[key] = value[:63]

    return labels


async def ssh_custom_forward(spawner, port_forward_info):
    custom_config = get_custom_config()
    remote_service = port_forward_info["service"]  # ${HOSTNAME_I}:${PORT}
    if spawner.internal_ssl:
        proto = "https://"
    else:
        proto = "http://"
    if remote_service.startswith(proto):
        remote_service = remote_service[len(proto) :]
    remote_svc_name, remote_svc_port = remote_service.split(":")
    local_svc_name = spawner.server.ip
    local_svc_port = spawner.server.port
    if not local_svc_name:
        local_svc_name = spawner.svc_name
    local_svc_name = local_svc_name.split(".")[0]
    if "ssh_node" in port_forward_info.keys():
        ssh_node = port_forward_info["ssh_node"]  # ${HOSTNAME_I}
    else:
        system = spawner.user_options.get("system", "unknown_system")
        ssh_node = f"outpost_{system.lower()}"

    labels = await spawner.get_extra_labels()

    body = {
        "hostname": ssh_node,
        "servername": spawner.name,
        "jhub_userid": spawner.user.id,
        "svc_name": local_svc_name,
        "svc_port": local_svc_port,
        "target_node": remote_svc_name,
        "target_port": remote_svc_port,
    }

    basic_auth = os.environ.get("TUNNEL_AUTHENTICATION_TOKEN", "None")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {basic_auth}",
        "uuidcode": spawner.name,
        "labels": json.dumps(labels),
    }

    # Why are labels not in body? This may be a TODO

    service_url = (
        custom_config.get("backendServices", {})
        .get("tunnel", {})
        .get("urls", {})
        .get("tunnel", "None")
    )

    request_kwargs = (
        custom_config.get("backendServices", {})
        .get("tunnel", {})
        .get("requestKwargs", {"request_timeout": 20})
    )

    req = HTTPRequest(
        url=service_url,
        method="POST",
        headers=headers,
        body=json.dumps(body),
        **request_kwargs,
    )

    await spawner.send_request(req, action="setuptunnel")
    return local_svc_name, local_svc_port


async def ssh_custom_forward_remove(spawner, *args, **kwargs):
    custom_config = get_custom_config()

    base_url = (
        custom_config.get("backendServices", {})
        .get("tunnel", {})
        .get("urls", {})
        .get("tunnel", "None")
    )
    request_kwargs = (
        custom_config.get("backendServices", {})
        .get("tunnel", {})
        .get("requestKwargs", {"request_timeout": 20})
    )
    if not base_url.endswith("/"):
        base_url += "/"
    url = f"{base_url}{spawner.name}/"
    basic_auth = os.environ.get("TUNNEL_AUTHENTICATION_TOKEN", "None")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {basic_auth}",
        "uuidcode": spawner.name,
    }
    req = HTTPRequest(
        url=url,
        method="DELETE",
        headers=headers,
        **request_kwargs,
    )
    await spawner.send_request(req, action="removetunnel")


async def is_system_allowed(spawner, user_options):
    # To check if the start procedure is allowed, we'll check if
    # - system is not in maintenace (JSC status page)
    # - system is allowed for user's group
    # - [service|system]_limit for user is not exceeded
    user = spawner.user
    named_spawners = list(spawner.user.all_spawners(include_default=False))
    custom_config = get_custom_config()

    auth_state = await user.get_auth_state()
    user_groups = auth_state["groups"]

    service = user_options["service"]
    option = user_options["option"]
    profile = user_options["profile"]
    system = user_options.get("system", "")
    # Let's check if the system is in maintenance
    incidents_dict = get_incidents()
    threshold_health = (
        custom_config.get("incidentCheck", {})
        .get("healthThreshold", {})
        .get("interactive", 0)
    )
    system_health = incidents_dict.get(system, {}).get("health", threshold_health - 1)
    if system_health >= threshold_health:
        # System is in maintenance
        raise Exception(
            f"System is currently in maintenance. Current health level: {system_health} (threshold: {threshold_health})"
        )

    service_limit = 0
    for group in user_groups:
        limit = (
            custom_config.get("services", {})
            .get(service, {})
            .get("options", {})
            .get(option, {})
            .get("maxPerUser", {})
            .get(group, 0)
        )
        if limit > service_limit:
            service_limit = limit
    if service_limit:
        current = 0
        for spawner in named_spawners:
            if (
                spawner
                and spawner.user_options
                and spawner.user_options.get("profile", "") == profile
                and spawner.active
            ):
                current += 1
        if current > service_limit:
            reason = f'User {user.name} already has the maximum number of {service_limit} servers with configuration "service - {profile}" running simultaneously. One must be stopped before a new server can be created'
            raise Exception(f"Service limit exceeded. {reason}")

    system_limit = 0
    for group in user_groups:
        limit = (
            custom_config.get("systems", {})
            .get(system, {})
            .get("maxPerUser", {})
            .get(group, 0)
        )
        if limit > system_limit:
            system_limit = limit
    if system_limit:
        current = 0
        for spawner in named_spawners:
            if (
                spawner
                and spawner.user_options
                and spawner.user_options.get("system", "") == system
                and spawner.active
            ):
                current += 1
        if current > system_limit:
            reason = f'User {user.name} already has the maximum number of {system_limit} servers with configuration "system - {system}" running simultaneously. One must be stopped before a new server can be created'
            raise Exception(f"Service limit exceeded. {reason}")


async def request_url(spawner, user_options):
    custom_config = get_custom_config()
    system = user_options.get("system", "None")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    url = (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("urls", {})
        .get("services", "None")
    )
    if url == "None":
        reason = f"JupyterHub configuration does not know backend-service {backend_service} (system {system}) or it has no url configured"
        raise Exception(reason)
    if not url.endswith("/"):
        url += "/"
    return url


async def request_headers(spawner, user_options):
    custom_config = get_custom_config()
    system = user_options.get("system", "None")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    auth = os.environ.get(f"AUTH_{backend_service.upper()}")
    headers = {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("sendAccessToken", False)
    ):
        send_access_token_key = (
            custom_config.get("backendServices", {})
            .get(backend_service, {})
            .get("sendAccessTokenKey", "Auth-State-access_token")
        )
        auth_state = await spawner.user.get_auth_state()
        headers[send_access_token_key] = auth_state.get("access_token", "None")
    return headers


def request_kwargs(spawner, user_options):
    custom_config = get_custom_config()
    system = user_options.get("system", "None")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    request_kwargs = (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("requestKwargs", {"request_timeout": 20})
    )
    return request_kwargs


async def custom_misc(spawner, user_options):
    pass


async def custom_env(spawner, user_options, jupyterhub_api_url):
    env = {}
    custom_config = get_custom_config()
    user_options_modules = spawner.user_options.get("modules", {})
    for module_type, modules in custom_config.get("userModules", {}).items():
        for module in modules:
            env[f"JUPYTER_MODULE_{module.upper()}_ENABLED"] = int(
                module in user_options_modules.get(module_type, [])
            )

    for envstring in spawner.user_options.get("envvariables", []):
        try:
            key, value = envstring.split("=")
            env[key] = value
        except:
            spawner.log.warning(
                f"{spawner.name} - env variable {envstring} cannot be used"
            )

    system = user_options.get("system", "")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    if (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("type", "kube")
    ):
        env[
            "JUPYTERHUB_FLAVORS_UPDATE_URL"
        ] = f"{jupyterhub_api_url.rstrip('/')}/outpostflavors/{system}"
        if os.environ.get("OUTPOST_FLAVORS_UPDATE_TOKEN", None):
            env["JUPYTERHUB_FLAVORS_UPDATE_TOKEN"] = os.environ.get(
                "OUTPOST_FLAVORS_UPDATE_TOKEN", ""
            )
    return env


def jhub_hostname():
    custom_config = get_custom_config()
    return custom_config.get("hostname", os.environ.get("JUPYTERHUB_HOSTNAME", "None"))


def custom_port(spawner, user_options):
    custom_config = get_custom_config()
    system = user_options.get("system", "None")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    port = (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("port", 8443)
    )
    return port


async def pre_poll_hook(spawner):
    custom_config = get_custom_config()
    system = spawner.user_options.get("system", "")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    if (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("pollAccessTokenRequired", False)
    ):
        # If we know we need need the access token to perform a valid poll request,
        # let's avoid the call to the Outpost if it's not helpful anyway.
        ret = await spawner.user.authenticator.refresh_user(spawner.user)
        if type(ret) == bool:
            return ret
        elif type(ret) == dict:
            # update auth state with new values
            if "auth_state" in ret.keys():
                await spawner.user.save_auth_state(ret["auth_state"])
                spawner.user._auth_refreshed = time.monotonic()
            return True
        else:
            spawner.log.info(
                f"Unknown return type of refresh_user: {type(ret)}. Return False"
            )
            return False
    return True


async def pre_stop_hook(spawner):
    global_sse = get_global_sse()
    global_sse.set()


async def pre_spawn_hook(spawner):
    global_sse = get_global_sse()
    global_sse.set()
    custom_config = get_custom_config()

    service = spawner.user_options["service"]
    for service_displayname, service_options in custom_config.get(
        "services", {}
    ).items():
        if service_options.get("serviceId", "") == service:
            service = service_displayname
    option = spawner.user_options["option"]
    system = spawner.user_options.get("system", "")
    default_version = (
        custom_config.get("systems", {})
        .get(system, {})
        .get("services", {})
        .get(service, {})
        .get("defaultOption", "")
    )
    if not default_version:
        default_version = (
            custom_config.get("services", {}).get(service, {}).get("defaultOption", "")
        )
    try:
        version_number = float(option)
        default_number = float(default_version)
        if version_number < default_number:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            deprecated_warning_event = {
                "failed": False,
                "ready": False,
                "progress": 15,
                "html_message": f'<details><summary>{now}: <span style="color:darkorange;">JupyterLab {option} is deprecated - you might want to switch to {default_version}</span></summary><p>JupyterLab versions < {default_version} are no longer actively supported even though they will be operational.</p></details>',
            }
            spawner.events.append(deprecated_warning_event)
    except ValueError:
        pass


async def post_spawn_request_hook(spawner, resp_json):
    db = inspect(spawner.user.orm_user).session
    get_user_count(db, force=True)
    global_sse = get_global_sse()
    global_sse.set()


async def post_stop_hook(spawner):
    db = inspect(spawner.user.orm_user).session
    get_user_count(db, force=True)
    global_sse = get_global_sse()
    global_sse.set()

    from jupyterhub.orm import Share as orm_share
    from jupyterhub.orm import ShareCode as orm_share_code

    db.query(orm_share).filter_by(
        spawner_id=spawner.orm_spawner.id,
    ).delete()
    db.query(orm_share_code).filter_by(
        spawner_id=spawner.orm_spawner.id,
    ).delete()
    # Remove all shares with this notebook


async def progress_ready_hook(spawner, ready_event):
    url = ready_event["url"]
    ready_msg = f"Service {spawner.name} started."
    detail_msg = f'You will be redirected to <a href="{url}" target="_blank">{url}</a>'

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    ready_event[
        "html_message"
    ] = f"<details><summary>{now}: {ready_msg}</summary>{detail_msg}</a></details>"

    # Prevent multpiple logs of the same message with different timestamps
    append_event = True
    try:
        for event in getattr(spawner, "events", []):
            if ready_msg in event.get("html_message", "") and detail_msg in event.get(
                "html_message", ""
            ):
                append_event = False
                break
    except:
        spawner.log.exception(
            f"{spawner._log_name} - Could not check if event is already in events"
        )

    if append_event:
        spawner.events.append(ready_event)
    return ready_event


def poll_interval(spawner, user_options):
    custom_config = get_custom_config()
    system = user_options.get("system", "None")
    backend_service = (
        custom_config.get("systems", {}).get(system, {}).get("backendService", "None")
    )
    if (
        custom_config.get("backendServices", {})
        .get(backend_service, {})
        .get("poll", True)
    ):
        base_poll_interval = (
            custom_config.get("backendServices", {})
            .get(backend_service, {})
            .get("pollInterval", 30)
        )
        poll_interval_randomizer = (
            custom_config.get("backendServices", {})
            .get(backend_service, {})
            .get("pollIntervalRandomizer", 0)
        )
        poll_interval = 1e3 * base_poll_interval + random.randint(
            0, int(1e3 * poll_interval_randomizer)
        )
    else:
        poll_interval = 0
    return poll_interval


def filter_events(spawner, event):
    message = event.get("html_message", event.get("message", ""))

    # Mostly used in custom images, if image cannot be pulled
    if "Error: ImagePullBackOff" in message:
        image = spawner.user_options.get("image", "<unknown>")
        replace_event = {
            "progress": 99,
            "html_message": f"<details><summary>Stopping start attempt. Image not available.</summary>Could not pull image {image}. Please choose a different image.</details>",
        }
        asyncio.create_task(spawner.stop())
        return replace_event

    if message.startswith("<details><summary>"):
        # Assume format is correct if message starts with given html tags
        return event
    dates = list(find_dates(message, index=True))
    if len(dates) > 0:
        first_match = dates[0]  # Tuple (datetime object, index)
        start_index, end_index = first_match[1]
        # Remove existing log timestamp
        message = message[:start_index] + message[end_index:]
    # Prepend current datetime to original message
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if message.startswith(" "):
        message = f"{now}:{message}"
    else:
        message = f"{now}: {message}"
    # Replace original messages
    if event.get("html_message"):
        event["html_message"] = message
    if event.get("message"):
        event["message"] = message
    return event


async def custom_user_options(spawner, user_options):
    from ..orm.share import UserOptionsShares

    log_user_options = copy.deepcopy(user_options)
    if "share_id" in user_options.keys():
        r2d_image = user_options.get("repo2docker", {}).get("image", None)
        user_options = UserOptionsShares.find_by_share_id(
            spawner.user.db, user_options["share_id"]
        ).user_options
        if (
            r2d_image
            and user_options.get("option", "") == "repo2docker"
            and "repo2docker" in user_options.keys()
        ):
            user_options["repo2docker"]["image"] = r2d_image

    ret = await recursive_decrypt(user_options.get("secret_keys", []), user_options)
    log_extras = {
        "userid": spawner.user.id,
        "username": spawner.user.name,
        "id": spawner.name,
        "startid": spawner.start_id,
        "user_options": log_user_options,
    }
    spawner.log.info(f"{spawner._log_name} - Start service", extra=log_extras)
    return ret
