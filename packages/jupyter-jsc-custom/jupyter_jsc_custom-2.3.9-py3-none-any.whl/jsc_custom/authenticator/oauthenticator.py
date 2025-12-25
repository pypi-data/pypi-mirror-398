import asyncio
import base64
import copy
import inspect
import json
import os
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode

from jupyterhub.utils import maybe_future
from jupyterhub.utils import new_token
from jupyterhub.utils import url_path_join
from oauthenticator.generic import GenericOAuthenticator
from oauthenticator.oauth2 import OAuthLoginHandler
from oauthenticator.oauth2 import OAuthLogoutHandler
from outpostspawner.api_flavors_update import get_user_specific_flavors
from tornado import web
from tornado.httpclient import HTTPClientError
from tornado.httpclient import HTTPRequest
from traitlets import Any
from traitlets import Callable
from traitlets import Dict
from traitlets import Unicode
from traitlets import Union

from ..misc import _custom_config_file
from ..misc import get_custom_config
from ..misc import get_last_incidents_change
from ..misc import get_last_reservation_change

res_pattern = re.compile(
    r"^urn:"
    r"(?P<namespace>.+?(?=:res:)):"
    r"res:"
    r"(?P<systempartition>[^:]+):"
    r"(?P<project>[^:]+):"
    r"act:"
    r"(?P<account>[^:]+):"
    r"(?P<accounttype>[^:]+)$"
)

res_groups_pattern = re.compile(
    r"^urn:"
    r"(?P<namespace>.+?(?=:res:)):"
    r"res:"
    r"(?P<parentgroup>[^:]+)?"
    r"(?::(?!role=)(?P<childgroup>[^:#]+))?"
    r"(?::(?!role=)(?P<grandchildgroup>[^:#]+))?"
    r"(?::role=(?P<role>[^#]+))?"
    r"#(?P<authority>.+)$"
)

group_pattern = re.compile(
    r"^urn:"
    r"(?P<namespace>.+?(?=:group:)):"
    r"group:"
    r"(?P<parentgroup>[^:]+)?"
    r"(?::(?!role=)(?P<childgroup>[^:#]+))?"
    r"(?::(?!role=)(?P<grandchildgroup>[^:#]+))?"
    r"(?::role=(?P<role>[^#]+))?"
    r"#(?P<authority>.+)$"
)


class VoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def get_groups_default(user_info):
    """
    Return all groups a user is part of
    JSC Login uses eduPersonEntitlement for group memberships.
    Definition is listed here:
     - https://zenodo.org/record/6533400/files/AARC-G069%20Guidelines%20for%20expressing%20group%20membership%20and%20role%20information.pdf

    All users are also in the default group

    Example:
        urn:<namespace>:group:parentgroup:childgroup:grandchildgroup:role=somerole#authority

    User will be in 4 groups:
        -   urn:<namespace>:group:parentgroup:childgroup:grandchildgroup
        -   urn:<namespace>:group:parentgroup:childgroup:grandchildgroup:role=somerole
        -   urn:<namespace>:group:parentgroup:childgroup:grandchildgroup:role=somerole#authority
        -   urn:<namespace>:group:parentgroup:childgroup:grandchildgroup#authority
        -   urn:<namespace>:group:parentgroup:childgroup
        -   urn:<namespace>:group:parentgroup:childgroup#authority
        -   urn:<namespace>:group:parentgroup
        -   urn:<namespace>:group:parentgroup#authority
        -   default
    """
    entitlements = user_info.get(
        "entitlements", user_info.get("oauth_user", {}).get("entitlements", [])
    )
    groups = []

    def add_sub_groups(group, role, authority, rightmost_group=True):
        if role and rightmost_group:
            group_role = f"{group}:role={role}"
            if group_role not in groups:
                groups.append(group_role)
        if authority:
            group_authority = f"{group}#{authority}"
            if group_authority not in groups:
                groups.append(group_authority)
        if role and rightmost_group and authority:
            group_role_authority = f"{group}:role={role}#{authority}"
            if group_role_authority not in groups:
                groups.append(group_role_authority)

    for entry in entitlements:
        match = group_pattern.match(entry)
        if match:
            namespace = match.group("namespace")
            grandchildgroup = match.group("grandchildgroup")
            childgroup = match.group("childgroup")
            parentgroup = match.group("parentgroup")
            role = match.group("role")
            authority = match.group("authority")
            rightmost_group = True
            if grandchildgroup:
                group = f"urn:{namespace}:group:{parentgroup}:{childgroup}:{grandchildgroup}"
                if group not in groups:
                    groups.append(group)
                add_sub_groups(group, role, authority, rightmost_group)
                rightmost_group = False
            if childgroup:
                group = f"{namespace}:{parentgroup}:{childgroup}"
                if group not in groups:
                    groups.append(group)
                add_sub_groups(group, role, authority, rightmost_group)
                rightmost_group = False
            if parentgroup:
                group = f"{namespace}:{parentgroup}"
                if group not in groups:
                    groups.append(group)
                add_sub_groups(group, role, authority, rightmost_group)
                rightmost_group = False
        else:
            match = res_groups_pattern.match(entry)
            if match:
                namespace = match.group("namespace")
                grandchildgroup = match.group("grandchildgroup")
                childgroup = match.group("childgroup")
                parentgroup = match.group("parentgroup")
                role = match.group("role")
                authority = match.group("authority")
                rightmost_group = True
                if grandchildgroup:
                    group = f"urn:{namespace}:group:{parentgroup}:{childgroup}:{grandchildgroup}"
                    if group not in groups:
                        groups.append(group)
                    add_sub_groups(group, role, authority, rightmost_group)
                    rightmost_group = False
                if childgroup:
                    group = f"{namespace}:{parentgroup}:{childgroup}"
                    if group not in groups:
                        groups.append(group)
                    add_sub_groups(group, role, authority, rightmost_group)
                    rightmost_group = False
                if parentgroup:
                    group = f"{namespace}:{parentgroup}"
                    if group not in groups:
                        groups.append(group)
                    add_sub_groups(group, role, authority, rightmost_group)
                    rightmost_group = False

    if "default" not in groups:
        groups.append("default")

    for attribute in ["org_domain", "voperson_external_affiliation"]:
        value = user_info.get(
            attribute, user_info.get("oauth_user", {}).get(attribute, None)
        )
        if value and type(value) == list:
            groups.extend(value)
        elif value and type(value) == str:
            groups.append(value)

    return list(set(groups))


class CustomLogoutHandler(OAuthLogoutHandler):
    """
    Default JupyterHub logout mechanism is a bit limited.
    This class allows us to do the followings (optional):
        - logout on all devices (by creating a new cookie_id)
        - stop all running services

    Both options can be triggered by url arguments
        - ?alldevices=true&stopall=true

    Next to this optional features, it also handles the oauth tokens.
    It always revokes the current access tokens.
    It revokes the refresh token if both conditions are true:
        - user logs out from all devices
        - stops all running services, or has none running

    """

    async def handle_logout(self):
        user = self.current_user
        if not user:
            self.log.debug("Could not retrieve current user for logout call.")
            return

        all_devices = self.get_argument("alldevices", "false").lower() == "true"
        stop_all = self.get_argument("stopall", "false").lower() == "true"
        # Stop all servers before revoking tokens
        if stop_all:
            await self._shutdown_servers(user)

        if user.authenticator.enable_auth_state:
            tokens = {}
            auth_state = await user.get_auth_state()
            access_token = auth_state.get("access_token", None)
            if access_token:
                tokens["access_token"] = access_token
                auth_state["access_token"] = None
                auth_state["exp"] = "0"
            # Only revoke refresh token if we logout from all devices and stop all services
            if all_devices and (stop_all or not user.active):
                refresh_token = auth_state.get("refresh_token", None)
                if refresh_token:
                    tokens["refresh_token"] = refresh_token
                    auth_state["refresh_token"] = None

            revocation_url = user.authenticator.revocation_url
            end_session_url = user.authenticator.end_session_url
            revocation_type = user.authenticator.revocation_type
            if not revocation_url:
                revocation_url = url_path_join(
                    user.authenticator.token_url.rstrip("/token"), "revoke"
                )
            client_id = user.authenticator.client_id
            unity_revoke_config = get_custom_config().get("unity", {}).get("revoke", {})
            unity_revoke_request_kwargs = unity_revoke_config.get(
                "requestKwargs", {"request_timeout": 10}
            )

            headers = {}
            data = {}

            if revocation_type.lower() == "infraproxy":
                client_secret = user.authenticator.client_secret
                basic_auth = base64.b64encode(
                    f"{client_id}:{client_secret}".encode("utf-8")
                ).decode("utf-8")
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_auth}",
                }
                data = {"client_id": client_id}
            elif revocation_type.lower() == "unity":
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                data = {"client_id": client_id, "logout": "true"}

            log_extras = {
                "unity_revoke_request_kwargs": unity_revoke_request_kwargs,
                "data": copy.deepcopy(data),
            }

            revoke_urls = []
            if end_session_url:
                revoke_urls.append(end_session_url)
            revoke_urls.append(revocation_url)

            for revoke_url in revoke_urls:
                for key, value in tokens.items():
                    data["token_type_hint"] = key
                    data["token"] = value
                    log_extras["revoke_url"] = revoke_url
                    log_extras["data"]["token_type_hint"] = key
                    log_extras["data"]["token"] = "***"
                    try:
                        req = HTTPRequest(
                            f"{revoke_url}",
                            method="POST",
                            headers=headers,
                            body=urlencode(data),
                            **unity_revoke_request_kwargs,
                        )
                        resp = await user.authenticator.fetch(req)
                        if resp and resp.error:
                            raise Exception(
                                f"Received unexpected status code: {resp.code}: {resp.error}"
                            )
                    except (HTTPError, HTTPClientError):
                        self.log.critical(
                            f"{user.name} - Could not revoke token",
                            extra=log_extras,
                            exc_info=True,
                        )
                    except:
                        self.log.critical(
                            f"{user.name} - Could not revoke token.",
                            extra=log_extras,
                            exc_info=True,
                        )
                    else:
                        self.log.debug(
                            f"{user.name} - Unity call {revoke_url} {key} call successful.",
                            extra=log_extras,
                        )
            await user.save_auth_state(auth_state)

        # Set new cookie_id to invalidate previous cookies
        if all_devices:
            orm_user = user.orm_user
            orm_user.cookie_id = new_token()
            self.db.commit()

    async def get(self):
        await self.handle_logout()
        await self.default_handle_logout()
        path = self.get_argument("next", default=False)
        if path:
            self.redirect(url_path_join(self.hub.base_url, path), permanent=False)
        else:
            await self.render_logout_page()


class CustomLoginHandler(OAuthLoginHandler):
    """
    This LoginHandler adds a small feature to the default OAuthLoginHandler:

    - send url parameters to the oauth endpoint.

    Enables us to select the preselected Authenticator in Unity.
    For safety reasons, one has to configure the allowed "extra_params".

    Example::
        def extra_params(handler):
            return {
                "key": ["allowed1", "allowed2"]
            }
        c.Authenticator.extra_params_allowed_runtime = extra_params
    """

    def authorize_redirect(self, *args, **kwargs):
        extra_params = kwargs.setdefault("extra_params", {})
        if self.authenticator.extra_params_allowed_runtime:
            if callable(self.authenticator.extra_params_allowed_runtime):
                extra_params_allowed = self.authenticator.extra_params_allowed_runtime()
            else:
                extra_params_allowed = self.authenticator.extra_params_allowed_runtime
            extra_params.update(
                {
                    k[len("extra_param_") :]: "&".join([x.decode("utf-8") for x in v])
                    for k, v in self.request.arguments.items()
                    if k.startswith("extra_param_")
                    and set([x.decode("utf-8") for x in v]).issubset(
                        extra_params_allowed.get(k[len("extra_param_") :], [])
                    )
                }
            )
        extra_params["prompt"] = "consent"
        return super().authorize_redirect(*args, **kwargs)


class CustomGenericOAuthenticator(GenericOAuthenticator):
    """
    This Authenticator offers additional information in the user's auth_state.
    That's necessary for Jupyter at JSC, because we need the options_form and
    some other tools at the /hub/home site to skip the "Select Options" site.
    """

    login_handler = CustomLoginHandler
    logout_handler = CustomLogoutHandler

    tokeninfo_url = Unicode(
        allow_none=True,
        config=True,
        help="""The url retrieving information about the access token""",
    )

    revocation_url = Unicode(
        allow_none=True,
        config=True,
        help="""The url revoking the access token""",
    )

    end_session_url = Unicode(
        allow_none=True,
        config=True,
        help="""The url ending the session at the identity provider""",
    )

    revocation_type = Unicode(
        default_value="Unity",
        config=True,
        help="""Two different types of token revocation: Unity or NFDI InfraProxy""",
    )

    extra_params_allowed_runtime = Union(
        [Dict(), Callable()],
        config=True,
        help="""Allowed extra GET params to send along with the initial OAuth request
        to the OAuth provider.
        Usage: GET to localhost:8000/hub/oauth_login?extra_param_<key>=<value>
        This argument defines the allowed keys and values.
        Example:
        ```
        {
            "key": ["value1", "value2"],
        }
        ```
        All accepted extra params will be forwarded without the `extra_param_` prefix.
        """,
    )

    outpost_flavors_auth = Any(
        help="""
        An optional hook function you can implement to define the body
        send to the JupyterHub Outpost, when pulling user specific
        flavors. The value returned by this function, can be used by the
        JupyterHub Outpost to define user specific flavors.
        
        Only used if user specific flavors are configured for a system.
        
        This may be a coroutine.
        
        Example::
        
            async def outpost_flavors_auth(system_name, authentication_safe):
                ret = {
                    "access_token": authentication_safe["auth_state"].get("access_token", ""),
                    "name": authentication_safe["auth_state"].get("name", ""),
                    "groups": authentication_safe["auth_state"].get("groups", []),
                }
                return ret
            
            c.OutpostSpawner.outpost_flavors_auth = outpost_flavors_auth
        """,
        default_value=False,
    ).tag(config=True)

    async def get_user_groups(self, user_info):
        list_ = await maybe_future(super().get_user_groups(user_info))
        return list(list_)

    auth_state_groups_key = Any(
        default_value=get_groups_default,
        help="""
        Userdata groups claim key from returned json for USERDATA_URL.

        Can be a string key name (use periods for nested keys), or a callable
        that accepts the returned json (as a dict) and returns the groups list.

        This configures how group membership in the upstream provider is determined
        for use by `allowed_groups`, `admin_groups`, etc. If `manage_groups` is True,
        this will also determine users' _JupyterHub_ group membership.
        """,
    ).tag(config=True)

    # DEPRECATED with oauthenticator>=17.0.0
    claim_groups_key = Any(
        default_value=get_groups_default,
        help="""
        Userdata groups claim key from returned json for USERDATA_URL.

        Can be a string key name (use periods for nested keys), or a callable
        that accepts the returned json (as a dict) and returns the groups list.

        This configures how group membership in the upstream provider is determined
        for use by `allowed_groups`, `admin_groups`, etc. If `manage_groups` is True,
        this will also determine users' _JupyterHub_ group membership.
        """,
    ).tag(config=True)

    def get_callback_url(self, handler=None):
        # Replace _host_ in callback_url with current request
        # Allows us to support multiple hostnames and redirect
        # to the used one.
        ret = super().get_callback_url(handler)
        if self.oauth_callback_url and handler and "_host_" in ret:
            ret = ret.replace("_host_", handler.request.host)
        return ret

    def user_info_to_username(self, user_info, refresh=False):
        username = super().user_info_to_username(user_info)
        normalized_username = self.normalize_username(username)
        blocklist_path = os.environ.get(
            "BLOCKLIST_PATH", "/mnt/shared-data/blocklist/blocklist.json"
        )
        if os.path.exists(blocklist_path):
            with open(blocklist_path, "r") as f:
                d = json.load(f)
            for key, value in user_info.items():
                if value in d.get(key, []):
                    self.log.info(
                        f"Login {normalized_username} - Blocked Login. {key}: {value}"
                    )
                    raise web.HTTPError(
                        403,
                        "Your account has been blacklisted due to resource misuse. If you believe this is a mistake, please contact support.",
                    )

        if refresh:
            self.log.debug(
                f"Refresh {username}",
                extra={
                    "action": "refresh",
                    "username": username,
                    "userinfo": user_info,
                },
            )
        else:
            self.log.info(
                f"Login {username}",
                extra={"action": "login", "username": username, "userinfo": user_info},
            )
        return username

    async def refresh_user(self, user, handler=None):
        auth_state = await user.get_auth_state()
        if not auth_state:
            return False
        authentication = {"auth_state": auth_state}
        ret = True
        now = time.time()
        rest_time = int(auth_state.get("exp", now)) - now
        if self.auth_refresh_age > rest_time:
            ## New access token required
            try:
                last_idp_save = auth_state.get("oauth_user", {}).get("last_idp", None)
                refresh_token_save = auth_state.get("refresh_token", None)
                self.log.debug(
                    f"{user.name} - Refresh authentication. Rest time: {rest_time}"
                )
                if not refresh_token_save:
                    self.log.debug(
                        f"{user.name} - Auth state has no refresh token. Return False."
                    )
                    return False
                params = {
                    "refresh_token": auth_state.get("refresh_token"),
                    "grant_type": "refresh_token",
                    "scope": " ".join(self.scope),
                }

                token_info = await self.get_token_info(handler, params)
                # use the access_token to get userdata info
                user_info = await self.token_to_user(token_info)
                if "last_idp" not in user_info.keys() and last_idp_save:
                    user_info["last_idp"] = last_idp_save
                # extract the username out of the user_info dict and normalize it
                username = self.user_info_to_username(user_info, refresh=True)
                username = self.normalize_username(username)

                authentication["name"] = username
                if not token_info.get("refresh_token", None):
                    token_info["refresh_token"] = refresh_token_save

                authentication["auth_state"] = self.build_auth_state_dict(
                    token_info, user_info
                )
                ret = await self.run_post_auth_hook(handler, authentication)
            except:
                self.log.exception(f"{user.name} - Refresh of access token failed")
                try:
                    self.log.error(f"Requesting access token from {self.token_url}")
                    x = urlencode(params).encode("utf-8")
                    y = self.build_token_info_request_headers()
                    self.log.error(f"Request params: {x}")
                    self.log.error(f"Request headers: {y}")
                except:
                    pass
                ret = False
        return ret

    async def run_outpost_flavors_auth(self, system_name, authentication_safe):
        if self.outpost_flavors_auth:
            ret = self.outpost_flavors_auth(system_name, authentication_safe)
            if inspect.isawaitable(ret):
                ret = await ret
        else:
            ret = {
                "access_token": authentication_safe["auth_state"].get(
                    "access_token", ""
                ),
                "name": authentication_safe["auth_state"].get("name", ""),
                "groups": authentication_safe["auth_state"].get("groups", []),
            }
        for key, value in (
            authentication_safe.get("auth_state", {}).get("oauth_user", {}).items()
        ):
            if key not in ret.keys():
                ret[key] = value
        return ret

    async def post_auth_hook(self, authenticator, handler, authentication):
        # After the user was authenticated we collect additional information
        #  - expiration of access token (so we can renew it before it expires)
        #  - last login (additional information for the user)
        #  - used authenticator (to classify user)
        #  - hpc_list (allowed systems, projects, partitions, etc.)
        if self.tokeninfo_url:
            access_token = authentication["auth_state"]["access_token"]
            headers = {
                "Accept": "application/json",
                "User-Agent": "JupyterHub",
                "Authorization": f"Bearer {access_token}",
            }
            req = HTTPRequest(self.tokeninfo_url, method="GET", headers=headers)
            try:
                resp = await authenticator.fetch(req)
            except HTTPClientError as e:
                authenticator.log.warning(
                    "{name} - Could not request user information - {e}".format(
                        name=authentication.get("name", "unknownName"), e=e
                    )
                )
                raise Exception(e)
            authentication["auth_state"]["exp"] = resp.get("exp")
        else:
            expires_in = (
                authentication.get("auth_state", {})
                .get("token_response", {})
                .get("expires_in", 600)
            )
            authentication["auth_state"]["exp"] = time.time() + expires_in

        preferred_username = (
            authentication["auth_state"]
            .get(self.user_auth_state_key, {})
            .get("preferred_username", None)
        )
        if preferred_username:
            authentication["auth_state"]["preferred_username"] = preferred_username
        # authentication["auth_state"]["entitlements"] = (
        #    authentication.get("auth_state", {})
        #    .get(self.user_auth_state_key, {})
        #    .get("entitlements", [])
        # )
        if handler:
            handler.statsd.incr(f"login.preferred_username.{preferred_username}")

        authentication["auth_state"]["name"] = authentication["name"]
        # In this part we classify the user in specific groups.
        try:
            groups_ = await self.get_user_groups(
                authentication["auth_state"][self.user_auth_state_key]
            )
            authentication["auth_state"]["groups"] = groups_
            authentication["groups"] = groups_
        except VoException as e:
            self.log.warning(
                "{name} - Could not get groups for user - {e}".format(
                    name=authentication.get("name", "unknownName"), e=e
                )
            )
            raise e

        try:
            user_specific_flavors = await self.collect_flavors_from_outposts(
                authentication
            )
            authentication["auth_state"]["outpost_flavors"] = user_specific_flavors
        except:
            self.log.exception(
                "Could not check user specific flavors. Use default flavors"
            )
        self.log.info(
            "Authenticated user {name} with groups".format(
                name=authentication.get("name", "unknownName")
            ),
            extra={
                "action": "groups",
                "username": authentication.get("name", "unknownName"),
                "groups": authentication.get("groups", []),
            },
        )
        return authentication

    async def collect_flavors_from_outposts(self, authentication):
        custom_config = get_custom_config()

        # Systems can have the option "userflavors": true.
        # If that's the case we will send a request to the outpost, to
        # receive the allowed flavors for this specific user

        user_specific_flavor_systems = {}
        for system_name, system_config in custom_config.get("systems", {}).items():
            backend_service = system_config.get("backendService", None)
            if not backend_service:
                self.log.warning(
                    f"BackendService for {system_name} not configured. Skip"
                )
                continue
            service_config = custom_config.get("backendServices", {}).get(
                backend_service, {}
            )
            if service_config.get("userflavors", False):
                services_url = service_config.get("urls", {}).get("services", None)
                if services_url:
                    url = services_url[: -len("services")] + "userflavors"
                else:
                    self.log.warning(
                        f"OutpostFlavors user specific - service url not defined. Skip {system_name}"
                    )
                    continue

                authentication_safe = copy.deepcopy(authentication)
                if "refresh_token" in authentication_safe.get("auth_state", {}).keys():
                    del authentication_safe["auth_state"]["refresh_token"]
                if "refresh_token" in authentication_safe.keys():
                    del authentication_safe["refresh_token"]
                authentication_used = await self.run_outpost_flavors_auth(
                    system_name, authentication_safe
                )
                if not service_config.get("sendAccessToken", False):
                    # Do not use accessToken in this request, if not configured in config
                    if (
                        "access_token"
                        in authentication_used.get("auth_state", {}).keys()
                    ):
                        del authentication_used["auth_state"]["access_token"]
                    if "access_token" in authentication_used.keys():
                        del authentication_used["access_token"]
                auth = os.environ.get(f"AUTH_{backend_service.upper()}")
                headers = {
                    "Authorization": f"Basic {auth}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                user_specific_flavor_systems[system_name] = {
                    "url": url,
                    "headers": headers,
                    "body": authentication_used,
                }
        ret = await get_user_specific_flavors(self.log, user_specific_flavor_systems)
        return ret
