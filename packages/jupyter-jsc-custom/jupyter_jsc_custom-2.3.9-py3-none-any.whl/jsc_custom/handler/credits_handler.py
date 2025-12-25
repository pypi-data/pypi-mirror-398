from datetime import timedelta

from jupyterhub.handlers import default_handlers
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.orm import utcnow
from jupyterhub_credit_service.orm import CreditsUser
from tornado import web


class CreditsHandler(BaseHandler):
    def format_duration(self, total_seconds):
        if (
            total_seconds is None
            or not isinstance(total_seconds, (int, float))
            or total_seconds < 0
        ):
            return "0s"
        seconds = int(total_seconds)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        return " ".join(parts)

    @web.authenticated
    async def get(self):
        user = self.current_user
        creditsuser = CreditsUser.get_user(user.authenticator.parent.db, user.name)
        ns = {"credits": {}}
        for cuv in creditsuser.credits_user_values:
            if cuv.user_options and cuv.user_options.get("system", None):
                key = cuv.user_options["system"]
                next_update_dt = cuv.grant_last_update + timedelta(
                    seconds=cuv.grant_interval
                )
                remaining_seconds1 = (next_update_dt - utcnow()).total_seconds()
                remaining_seconds2 = (
                    remaining_seconds1 + user.authenticator.credits_task_interval
                )
                next_update1 = self.format_duration(remaining_seconds1)
                next_update2 = self.format_duration(remaining_seconds2)
                value = {
                    "balance": cuv.balance,
                    "cap": cuv.cap,
                    "grant_value": cuv.grant_value,
                    "grant_interval": self.format_duration(cuv.grant_interval),
                    "grant_last_update": cuv.grant_last_update,
                    "grant_next_update": f"between {next_update1} and {next_update2}",
                }
                if cuv.project:
                    next_update_dt = cuv.project.grant_last_update + timedelta(
                        seconds=cuv.project.grant_interval
                    )
                    remaining_seconds1 = (next_update_dt - utcnow()).total_seconds()
                    remaining_seconds2 = (
                        remaining_seconds1 + user.authenticator.credits_task_interval
                    )
                    next_update1 = self.format_duration(remaining_seconds1)
                    next_update2 = self.format_duration(remaining_seconds2)
                    value["project"] = {
                        "name": cuv.project.name,
                        "balance": cuv.project.balance,
                        "cap": cuv.project.cap,
                        "grant_value": cuv.project.grant_value,
                        "grant_interval": self.format_duration(
                            cuv.project.grant_interval
                        ),
                        "grant_last_update": cuv.project.grant_last_update,
                        "grant_next_update": f"between {next_update1} and {next_update2}",
                    }
                ns["credits"][key] = value
        html = await self.render_template("credits.html", **ns)
        self.finish(html)


default_handlers.append((r"/credits", CreditsHandler))
