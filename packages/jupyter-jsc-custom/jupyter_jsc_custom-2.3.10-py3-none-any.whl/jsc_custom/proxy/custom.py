import json

from jupyterhub_traefik_proxy import traefik_utils as traefik_utils_orig
from jupyterhub_traefik_proxy.etcd import TraefikEtcdProxy
from jupyterhub_traefik_proxy.kv_proxy import TKvProxy
from tornado.httpclient import HTTPClientError
from traitlets import Bool
from traitlets import Dict
from traitlets import List
from traitlets import Unicode


class SSLTKvProxy(TKvProxy):
    traefik_tls_options = Dict(
        default_value=None,
        allow_none=True,
        config=True,
        help="""
        A dictionary of traefik TLS options to apply to services when using internal SSL.
        This can be used to customize the TLS settings used by traefik when communicating
        with backends over SSL.
        Example: {"options": "default"},
        """,
    )
    traefik_router_middlewares = List(
        default_value=[],
        allow_none=True,
        config=True,
        help="""
        A list of traefik middleware names to add to each router for retrying requests.
        This can be used to improve reliability when using traefik with backends that may intermittently fail.
        """,
    )

    skip_hub_route = Bool(
        False,
        config=True,
        help="If True, skip adding a route for the hub itself",
    )

    skip_services_route = Bool(
        False,
        config=True,
        help="If True, skip adding a route for services",
    )

    traefik_http_servers_transport = Unicode(
        "",
        allow_none=True,
        config=True,
        help="The name of the servers transport to use for internal SSL",
    )

    traefik_alias_prefix = Unicode(
        "",
        config=True,
        help="""The alias prefix to use for traefik services.

        This is used to namespace the services created by traefik,
        to avoid conflicts with other services running in the same
        environment.
        """,
    )

    traefik_enforce_host_in_rules = Unicode(
        "",
        config=True,
        help="""
        Optional configuration to enforce a specific host in all generated traefik rules.
        Allows running multiple JupyterHub instances behind the same traefik proxy.
        """,
    )

    def generate_rule(self, routespec):
        rule = traefik_utils_orig.generate_rule(routespec)
        if (not rule.startswith("Host")) and self.traefik_enforce_host_in_rules:
            return f"Host(`{self.traefik_enforce_host_in_rules}`) && {rule}"
        else:
            return rule

    def generate_alias(self, routespec, kind=""):
        alias = traefik_utils_orig.generate_alias(routespec, kind)
        if self.traefik_alias_prefix:
            return f"{self.traefik_alias_prefix}_{alias}"
        else:
            return alias

    async def add_route(self, routespec, target, data=None):
        if data.get("hub", False) and self.skip_hub_route:
            return
        if routespec.startswith("/services/") and self.skip_services_route:
            return
        await super().add_route(routespec, target, data)

    async def _check_for_traefik_service(self, routespec, kind):
        """Check for an expected router or service in the Traefik API.

        This is used to wait for traefik to load configuration
        from a provider
        """
        # expected e.g. 'service' + '_' + routespec @ file
        routespec = self.validate_routespec(routespec)
        expected = self.generate_alias(routespec, kind) + "@" + self.provider_name
        path = f"/api/http/{kind}s/{expected}"
        try:
            resp = await self._traefik_api_request(path)
            json.loads(resp.body)
        except HTTPClientError as e:
            if e.code == 404:
                self.log.debug(
                    "Traefik route for %s: %s not yet in %s", routespec, expected, kind
                )
                return False
            self.log.exception(f"Error checking traefik api for {kind} {routespec}")
            return False
        except Exception:
            self.log.exception(f"Error checking traefik api for {kind} {routespec}")
            return False

        # found the expected endpoint
        return True

    def _dynamic_config_for_route(self, routespec, target, data):
        """Returns two dicts, which will be used to update traefik configuration for a given route

        (traefik_config, jupyterhub_config) -
            where traefik_config is traefik dynamic_config to be merged,
            and jupyterhub_config is jupyterhub-specific data to be stored elsewhere
            (implementation-specific) and associated with the route
        """

        service_alias = self.generate_alias(routespec, "service")
        router_alias = self.generate_alias(routespec, "router")
        rule = self.generate_rule(routespec)
        # dynamic config to deep merge
        traefik_config = {
            "http": {
                "routers": {},
                "services": {},
            },
        }

        jupyterhub_config = {
            "routes": {},
        }
        traefik_config["http"]["routers"][router_alias] = {
            "service": service_alias,
            "rule": rule,
            "entryPoints": [self.traefik_entrypoint],
        }
        if self.traefik_router_middlewares:
            traefik_config["http"]["routers"][router_alias][
                "middlewares"
            ] = self.traefik_router_middlewares
        traefik_config["http"]["services"][service_alias] = {
            "loadBalancer": {"servers": [{"url": target}], "passHostHeader": True}
        }
        if self.traefik_tls_options:
            traefik_config["http"]["routers"][router_alias][
                "tls"
            ] = self.traefik_tls_options
        if self.app.internal_ssl:
            if self.traefik_http_servers_transport:
                traefik_config["http"]["services"][service_alias]["loadBalancer"][
                    "serversTransport"
                ] = self.traefik_http_servers_transport

        # Add the data node to a separate top-level node, so traefik doesn't see it.
        # key needs to be key-value safe (no '/')
        # store original routespec, router, service aliases for easy lookup
        jupyterhub_config["routes"][router_alias] = {
            "data": data,
            "routespec": routespec,
            "target": target,
            "router": router_alias,
            "service": service_alias,
        }
        return traefik_config, jupyterhub_config

    def _keys_for_route(self, routespec):
        service_alias = self.generate_alias(routespec, "service")
        router_alias = self.generate_alias(routespec, "router")
        traefik_keys = (
            ["http", "routers", router_alias],
            ["http", "services", service_alias],
        )
        jupyterhub_keys = (["routes", router_alias],)
        return traefik_keys, jupyterhub_keys

    async def get_all_routes(self):
        if self._start_future and not self._start_future.done():
            await self._start_future

        jupyterhub_config = await self._get_jupyterhub_dynamic_config()

        all_routes = {}
        for _, route in jupyterhub_config.get("routes", {}).items():
            if self.traefik_alias_prefix and (
                not route.get("router", "").startswith(self.traefik_alias_prefix)
                and not route.get("service", "").startswith(self.traefik_alias_prefix)
            ):
                # not our route
                continue
            all_routes[route["routespec"]] = {
                "routespec": route["routespec"],
                "data": route.get("data", {}),
                "target": route["target"],
            }
        return all_routes

    async def get_route(self, routespec):
        routespec = self.validate_routespec(routespec)
        router_alias = self.generate_alias(routespec, "router")
        route_key = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "routes", router_alias]
        )
        route = await self._kv_get_tree(route_key)
        if not route:
            return None
        return {key: route[key] for key in ("routespec", "data", "target")}


class SSLTraefikEtcdProxy(SSLTKvProxy, TraefikEtcdProxy):
    pass
