import secrets
from datetime import datetime

from jupyterhub.apihandlers import APIHandler
from jupyterhub.apihandlers import default_handlers
from jupyterhub.scopes import needs_scope
from tornado import web

from ..misc import get_custom_config
from ..orm.workshops import WorkshopShares


def isInstructor(groups=[]):
    instructorGroup = (
        get_custom_config()
        .get("workshop", {})
        .get(
            "instructorGroup",
            "geant:dfn.de:fz-juelich.de:jsc:jupyter:workshop_instructors",
        )
    )
    if instructorGroup in groups:
        return True
    else:
        return False


class WorkshopManagerAPIHandler(APIHandler):
    @needs_scope("servers")
    async def post(self, workshop_id=""):
        user = self.current_user
        if not user:
            raise web.HTTPError(403)
        auth_state = await user.get_auth_state()
        if not isInstructor(auth_state.get("groups", [])) and workshop_id:
            db_entry = WorkshopShares.find_by_workshop_id(
                self.db, workshop_id=workshop_id
            )
            if not db_entry:
                raise web.HTTPError(403)
            if db_entry.instructor_user_id != user.id:
                raise web.HTTPError(403)

        while not workshop_id:
            workshop_id = secrets.token_urlsafe(8)
            db_entry = WorkshopShares.find_by_workshop_id(
                self.db, workshop_id=workshop_id
            )
            if db_entry:
                # the entry already exists, create a new workshop id
                workshop_id = ""

        data = self.get_json_body()
        if not data.get("workshopid", False):
            data["workshopid"] = workshop_id

        db_entry = WorkshopShares.find_by_workshop_id(self.db, workshop_id=workshop_id)
        data["name"] = f"Workshop {workshop_id}"
        if db_entry is None:
            new_entry = WorkshopShares(
                workshop_id=workshop_id, instructor_user_id=user.id, user_options=data
            )
            self.db.add(new_entry)
            self.db.commit()
        elif db_entry.instructor_user_id == user.id:
            db_entry.user_options = data
            self.db.commit()
        else:
            raise web.HTTPError(
                400,
                "A workshop with this name already exists. Please choose a different name.",
            )

        self.set_status(200)
        self.set_header("Content-Type", "text/plain")
        self.write(workshop_id)

    @needs_scope("servers")
    async def delete(self, workshop_id):
        user = self.current_user
        if not user:
            raise web.HTTPError(403)
        db_entry = WorkshopShares.find_by_workshop_id(self.db, workshop_id=workshop_id)
        if db_entry is None:
            raise web.HTTPError(404)
        elif db_entry.instructor_user_id == user.id:
            self.db.delete(db_entry)
            self.db.commit()
        else:
            raise web.HTTPError(403)
        self.set_status(204)

    @needs_scope("servers")
    async def get(self, workshop_id=""):
        user = self.current_user
        if not user:
            raise web.HTTPError(403)

        ret = {}
        if workshop_id:
            db_entry = WorkshopShares.find_by_workshop_id(
                self.db, workshop_id=workshop_id
            )
            if db_entry is None:
                raise web.HTTPError(404)
            else:
                ret = db_entry.to_dict()
        else:
            db_entries = self.db.query(WorkshopShares)
            for db_entry in db_entries:
                ret[db_entry.workshop_id] = db_entry.to_dict()

        self.set_status(200)
        self.set_header("Content-Type", "text/plain")
        self.write(ret)


default_handlers.append((r"/api/workshops", WorkshopManagerAPIHandler))
default_handlers.append((r"/api/workshops/([^/]+)", WorkshopManagerAPIHandler))
