import copy
import secrets

from jupyterhub.apihandlers import APIHandler
from jupyterhub.apihandlers import default_handlers
from jupyterhub.scopes import needs_scope
from tornado import web

from ..orm.share import UserOptionsShares
from ..spawner.utils import EncryptJSONBody
from ..spawner.utils import recursive_decrypt


class ShareUserOptionsAPIHandler(EncryptJSONBody, APIHandler):
    @needs_scope("servers")
    async def post(self):
        user = self.current_user
        if not user:
            raise web.HTTPError(403)
        data = await self.async_get_json_body()
        if "share_id" in data.keys():
            del data["share_id"]
        db_entries = UserOptionsShares.list(self.db)

        share_id = None
        try:
            user_options_decrypted = await recursive_decrypt(
                data.get("secret_keys", []), copy.deepcopy(data), False
            )
            for db_entry in db_entries:
                db_entry_decrypted = await recursive_decrypt(
                    db_entry.user_options.get("secret_keys", []),
                    db_entry.user_options,
                    False,
                )
                if user_options_decrypted == db_entry_decrypted:
                    share_id = db_entry.share_id
                    break

            if share_id is None:
                share_id = secrets.token_urlsafe(8)
                new_entry = UserOptionsShares(
                    share_id=share_id, user_options=data, user_id=user.orm_user.id
                )
                self.db.add(new_entry)
                self.db.commit()

            self.set_status(200)
            self.set_header("Content-Type", "text/plain")
            self.write(share_id)
        except:
            self.log.exception("Error while looking for share id")
            self.set_status(400)


default_handlers.append((r"/api/share/user_options", ShareUserOptionsAPIHandler))
