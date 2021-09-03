"""Main application file.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

import base64

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from . import config, database, describers, identifiers, session


async def make_app() -> web.Application:
    """Create the app."""
    app = web.Application()

    app.on_startup.append(database.startup)
    app.on_cleanup.append(database.cleanup)

    # secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app,
          EncryptedCookieStorage(secret_key, cookie_name=config.COOKIE_NAME))

    app.add_routes([
        web.get("/", describers.root),
        web.get("/user", describers.user),
        web.post("/user/login", session.login),
        web.post("/user/password", session.password),
        web.post("/user/create", session.create),
        web.get("/identifiers", describers.identifiers),
        web.get("/identifiers/get", identifiers.get),
        web.post("/identifiers/insert", identifiers.insert),
        web.put("/identifiers/update", identifiers.update),
        web.post("/identifiers/upsert", identifiers.upsert),
        web.delete("/identifiers/remove", identifiers.remove),
    ], )
    return app
