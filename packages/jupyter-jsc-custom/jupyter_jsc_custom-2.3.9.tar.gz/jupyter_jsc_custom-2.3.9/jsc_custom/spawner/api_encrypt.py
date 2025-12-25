from jupyterhub.apihandlers import default_handlers
from jupyterhub.apihandlers.users import UserServerAPIHandler

from .utils import EncryptJSONBody


class EncryptedUserServerAPIHandler(EncryptJSONBody, UserServerAPIHandler):
    pass


default_handlers.append(
    (r"/api/users/([^/]+)/encryptedserver", EncryptedUserServerAPIHandler)
)
default_handlers.append(
    (r"/api/users/([^/]+)/encryptedservers/([^/]*)", EncryptedUserServerAPIHandler)
)
