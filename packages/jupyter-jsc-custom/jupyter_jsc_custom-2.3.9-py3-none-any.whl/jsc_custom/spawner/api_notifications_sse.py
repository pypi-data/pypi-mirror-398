import asyncio
import inspect
import sys

if sys.version_info >= (3, 10):
    from contextlib import aclosing
else:
    from async_generator import aclosing
from jupyterhub.apihandlers import default_handlers
from jupyterhub.apihandlers.users import SpawnProgressAPIHandler
from jupyterhub.utils import iterate_until
from jupyterhub.utils import url_escape_path
from jupyterhub.utils import url_path_join
from outpostspawner.api_flavors_update import async_get_flavors
from tornado.web import Finish

from ..apihandler.user_count import get_user_count
from ..misc import get_global_sse
from ..misc import get_incidents
from ..misc import get_reservations

from jupyterhub_credit_service.orm import CreditsUser

# References for tasks that cancel other tasks
cleanup_tasks_references = set()


class SSEAPIHandler(SpawnProgressAPIHandler):
    """EventStream handler to update the frontend if something changes on the backend"""

    keepalive_interval = 8
    keepalive_task = None
    watched_spawns = {}

    async def cancel_task(self, task):
        if not task.done():
            try:
                task.cancel()
                await task
            except (RuntimeError, StopAsyncIteration, asyncio.CancelledError):
                pass

    def on_finish(self):
        # Cancel all background tasks which are forwarding spawn progresses.
        # Run the cancel in the background, and remove the reference from this cancel_task
        for spawner_tasks in self.watched_spawns.values():
            for task in list(spawner_tasks.values()):
                task = asyncio.create_task(self.cancel_task(task))
                cleanup_tasks_references.add(task)
                task.add_done_callback(cleanup_tasks_references.discard)

        # Set finish future to done. Other threads might wait for it
        if not self._finish_future.done():
            self._finish_future.set_result(None)

        # Remove reference from keepalive task, so the garbage collector will do its job.
        self.keepalive_task = None

    async def get_global_event_data(self, user):
        event_data = {
            "usercount": get_user_count(self.db),
            "incidents": get_incidents(None),
        }
        if user:
            event_data["reservations"] = get_reservations()
            event_data["flavors"] = await async_get_flavors(self.log, user)
            mem_spawners = user.spawners.keys()
            orm_spawners = user.orm_user._orm_spawners
            stopped = [s.name for s in orm_spawners if s.name not in mem_spawners]
            stopping = []
            for spawner in user.spawners.values():
                if spawner.name:
                    if spawner.active and spawner.pending == "stop":
                        stopping.append(spawner.name)
                    elif not spawner.active:
                        stopped.append(spawner.name)
            event_data["servers"] = {"stopped": stopped, "stopping": stopping}
            if getattr(user.authenticator, "credits_enabled", False):
                try:
                    credits_list = []
                    credit_user = CreditsUser.get_user(
                        user.authenticator.parent.db, user.name
                    )
                    for credits in credit_user.credits_user_values:
                        credits_list.append(
                            {
                                "balance": credits.balance,
                                "cap": credits.cap,
                                "user_options": credits.user_options,
                            }
                        )
                        if credits.project:
                            credits_list[-1]["project"] = {
                                "balance": credits.project.balance,
                                "cap": credits.project.cap,
                                "user_options": credits.project.user_options,
                                "name": credits.project.name,
                            }
                except Exception as e:
                    self.log.exception(f"Error getting credits user: {e}")
                else:
                    event_data["credits"] = credits_list
        return event_data

    async def handle_spawner_progress(self, spawner):
        def format_event(event):
            return {"progress": {spawner.name: event}}

        failed_event = {"progress": 100, "failed": True, "message": "Spawn failed"}

        async def get_ready_event():
            url = url_path_join(spawner.user.url, url_escape_path(spawner.name), "/")
            ready_event = {
                "progress": 100,
                "ready": True,
                "message": f"Server ready at {url}",
                "html_message": 'Server ready at <a href="{0}">{0}</a>'.format(url),
                "url": url,
            }
            original_ready_event = ready_event.copy()
            try:
                ready_event = spawner.progress_ready_hook(spawner, ready_event)
                if inspect.isawaitable(ready_event):
                    ready_event = await ready_event
            except Exception as e:
                ready_event = original_ready_event
                self.log.exception(f"Error in ready_event hook: {e}")
            return ready_event

        if spawner.ready:
            # spawner already ready. Trigger progress-completion immediately
            self.log.info("Server %s is already started", spawner._log_name)
            ready_event = await get_ready_event()
            await self.send_event(format_event(ready_event))
            return

        spawn_future = spawner._spawn_future

        if not spawner._spawn_pending:
            # not pending, no progress to fetch
            # check if spawner has just failed
            f = spawn_future
            if f and f.cancelled():
                failed_event["message"] = "Spawn cancelled"
            elif f and f.done() and f.exception():
                exc = f.exception()
                message = getattr(exc, "jupyterhub_message", str(exc))
                failed_event["message"] = f"Spawn failed: {message}"
                html_message = getattr(exc, "jupyterhub_html_message", "")
                if html_message:
                    failed_event["html_message"] = html_message

            last_event = getattr(spawner, "last_event", None)
            if last_event is not None:
                last_event = last_event.copy()
            cancelling_event = await spawner.get_cancelling_event()
            if cancelling_event:
                await self.send_event(format_event(cancelling_event))
            if hasattr(spawner, "_stop_pending_event") and spawner._stop_pending_event:
                await spawner._stop_pending_event.wait()
            if last_event:
                await self.send_event(format_event(last_event))
            else:
                await self.send_event(format_event(failed_event))
            return

        # retrieve progress events from the Spawner
        async with aclosing(
            iterate_until(spawn_future, spawner._generate_progress())
        ) as events:
            try:
                async for event in events:
                    # don't allow events to sneakily set the 'ready' flag
                    if "ready" in event:
                        event.pop("ready", None)
                    if event.get("progress", 10) != 0:
                        await self.send_event(format_event(event))
            except asyncio.CancelledError:
                pass
            except Finish:
                pass

        await asyncio.wait([spawn_future])
        if spawner.ready and not (spawn_future and spawn_future.cancelled()):
            # spawner is ready, signal completion and redirect
            self.log.debug("Server %s is ready", spawner._log_name)
            ready_event = await get_ready_event()
            await self.send_event(format_event(ready_event))
        else:
            # what happened? Maybe spawn failed?
            f = spawn_future
            if f and f.cancelled():
                failed_event["message"] = "Spawn cancelled"
            elif f and f.done() and f.exception():
                exc = f.exception()
                message = getattr(exc, "jupyterhub_message", str(exc))
                failed_event["message"] = f"Spawn failed: {message}"
                html_message = getattr(exc, "jupyterhub_html_message", "")
                if html_message:
                    failed_event["html_message"] = html_message
            else:
                self.log.warning(
                    "Server %s didn't start for unknown reason", spawner._log_name
                )
            last_event = getattr(spawner, "last_event", None)
            if last_event is not None:
                last_event = last_event.copy()
            cancelling_event = await spawner.get_cancelling_event()
            if cancelling_event:
                await self.send_event(format_event(cancelling_event))
            if hasattr(spawner, "_stop_pending_event") and spawner._stop_pending_event:
                await spawner._stop_pending_event.wait()
            if last_event:
                await self.send_event(format_event(last_event))
            else:
                await self.send_event(format_event(failed_event))

    def spawn_watch_callback(self, user_id, spawner_name):
        if spawner_name in self.watched_spawns.get(user_id, {}).keys():
            task = self.watched_spawns[user_id].pop(spawner_name, None)
            if task:
                asyncio.create_task(self.cancel_task(task))

    async def event_handler(self, user=None):
        global_sse = get_global_sse()
        self.watched_spawns = {}
        if user:
            self.watched_spawns[user.orm_user.id] = {}

        while (
            type(self._finish_future) is asyncio.Future
            and not self._finish_future.done()
        ):
            if user:
                # Re-evaluate the active spawners list after an update
                spawning = {
                    s.name: s for s in user.spawners.values() if s.pending == "spawn"
                }
                for spawner_name, spawner in spawning.items():
                    # Looking for new spawners we have to watch
                    if spawner_name not in self.watched_spawns[user.orm_user.id].keys():
                        task = asyncio.ensure_future(
                            self.handle_spawner_progress(spawner)
                        )
                        self.watched_spawns[user.orm_user.id][spawner_name] = task
                        task.add_done_callback(
                            lambda t: self.spawn_watch_callback(
                                user.orm_user.id, spawner_name
                            )
                        )
            global_event = await self.get_global_event_data(user)
            try:
                yield global_event
            except GeneratorExit as e:
                raise e
            finally:
                global_sse.clear()
            await global_sse.wait()

    async def get(self, user_name=""):
        self.set_header("Cache-Control", "no-cache")
        if user_name:
            user = self.find_user(user_name)
        else:
            user = None
        # start sending keepalive to avoid proxies closing the connection
        # This task will be finished / done, once the tab in the browser is closed
        self.keepalive_task = asyncio.create_task(self.keepalive())

        try:
            async with aclosing(
                iterate_until(self.keepalive_task, self.event_handler(user))
            ) as events:
                async for event in events:
                    if event:
                        await self.send_event(event)
                    else:
                        break
        except (RuntimeError, StopAsyncIteration, asyncio.CancelledError):
            pass


default_handlers.append((r"/api/sse/([^/]+)", SSEAPIHandler))
default_handlers.append((r"/api/sse", SSEAPIHandler))
