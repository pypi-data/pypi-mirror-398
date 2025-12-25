import asyncio
import copy
import json

from jupyterhub.crypto import decrypt
from jupyterhub.crypto import encrypt
from tornado import web

from ..misc import Thread


async def recursive_encrypt(keysToEncrypt, json_dict):
    for key, value in json_dict.items():
        if type(value) == dict:
            json_dict[key] = await recursive_encrypt(keysToEncrypt, value)
        elif key in keysToEncrypt:
            byte_value = await encrypt(value)
            json_dict[key] = byte_value.decode("utf-8")
    return json_dict


async def recursive_decrypt(keysToDecrypt, json_dict, set_placeholder=False):
    for key, value in json_dict.items():
        if type(value) == dict:
            json_dict[key] = await recursive_decrypt(
                keysToDecrypt, value, set_placeholder
            )
        elif key in keysToDecrypt:
            if set_placeholder:
                json_dict[key] = "hiddenSecret"
            else:
                try:
                    json_dict[key] = await decrypt(value)
                except:
                    json_dict[key] = value
    return json_dict


class EncryptJSONBody:
    def get_json_body(self):
        loop = asyncio.new_event_loop()

        async def wait_for_future(future):
            return await future

        def t_encrypt(loop):
            asyncio.set_event_loop(loop)
            ret = loop.run_until_complete(wait_for_future(self.async_get_json_body()))
            return ret

        t = Thread(target=t_encrypt, args=(loop,))
        t.start()
        ret = t.join()
        return ret

    async def async_get_json_body(self):
        """Return the body of the request as JSON data."""
        if not self.request.body:
            return None
        body = self.request.body.strip().decode("utf-8")
        try:
            model = json.loads(body)
        except Exception:
            self.log.debug("Bad JSON: %r", body)
            self.log.error("Couldn't parse JSON", exc_info=True)
            raise web.HTTPError(400, "Invalid JSON in body of request")

        model = await recursive_encrypt(model.get("secret_keys", []), model)
        return model


def decrypted_user_options(user):
    if not user:
        return {}
    loop = asyncio.new_event_loop()

    async def wait_for_future(future):
        return await future

    def t_decrypt(loop, user):
        asyncio.set_event_loop(loop)
        ret = loop.run_until_complete(
            wait_for_future(async_decrypted_user_options(user))
        )
        return ret

    t = Thread(target=t_decrypt, args=(loop, user))
    t.start()
    ret = t.join()
    return ret


async def async_decrypted_user_options(user):
    try:
        decrypted_user_options = {}
        for orm_spawner in user.orm_user._orm_spawners:
            if not orm_spawner.user_options:
                decrypted_user_options[orm_spawner.name] = {}
                continue

            user_options = copy.deepcopy(orm_spawner.user_options)
            user_options = await recursive_decrypt(
                user_options.get("secret_keys", []),
                user_options,
                "share_id" in user_options.keys(),
            )
            decrypted_user_options[orm_spawner.name] = user_options
        return decrypted_user_options
    except:
        user.log.exception(f"Could not load decrypted user options {user.name}")
        return {}
