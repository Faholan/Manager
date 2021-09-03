"""Session managing.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

import json
from hashlib import pbkdf2_hmac, sha256
from os import urandom

from aiohttp import web
from aiohttp_session import new_session, get_session
from Crypto.Cipher import AES

from . import config
from .utils import authenticated, optional, required


@required(username=str, password=str)
async def login(request: web.Request) -> web.Response:
    """Implement login functionality.

    Required parameters:
    - username: string
    - password: string
    """
    data = await request.json()

    session = await new_session(request)
    session["remote"] = request.remote
    async with request.app["asyncpg.pool"].acquire() as database:
        row = await database.fetchrow(
            "SELECT * FROM sessions WHERE username=$1",
            data["username"]
        )

    if not row:
        raise web.HTTPForbidden(
            reason=f"User {data['username']} does not exist",
            text=json.dumps(
                {
                    "success": False,
                    "msg": f"User {data['username']} does not exist",
                    "error_code": "unknown_user"
                },
            )
        )

    pass_bytes = bytes(request["password"], "utf8")

    if pbkdf2_hmac(
        "sha256",
        pass_bytes,
        row["salt"],
        config.HASH_ITERATIONS
    ) != row["password"]:
        raise web.HTTPForbidden(
            reason="Wrong password",
            text=json.dumps(
                {
                    "success": False,
                    "msg": "Wrong password",
                    "error_code": "wrong_password",
                }
            )
        )
    session["id"] = row["id"]
    session["admin"] = row["admin"]

    session["password"] = sha256(pass_bytes).digest()

    return web.json_response({"success": True})


@authenticated
@required(password=str)
async def password(request: web.Request) -> web.Response:
    """Change your password.

    Required parameters:
    - password: string
    """
    data = await request.json()

    session = await get_session(request)

    salt = urandom(config.SALT_LENGTH)
    async with request.app["asyncpg.pool"].acquire() as database:
        await database.execute(
            "UPDATE sessions SET password=$2 AND salt=$3 WHERE id=$1",
            session["id"],
            salt,
            pbkdf2_hmac(
                "sha256",
                bytes(data["password"], "utf8"),
                salt,
                config.HASH_ITERATIONS
            )
        )
        new_pass = sha256(bytes(data["password"], "utf8")).digest()
        for row in await database.fetch(
            "SELECT * FROM identifiers WHERE id=$1",
            session["id"],
        ):
            await database.execute(
                "UPDATE identifiers SET password=$1 WHERE id=$2 AND context=$3 AND username=$4",
                AES.new(
                    new_pass,
                    AES.MODE_EAX,
                    nonce=row["nonce"],
                ).encrypt(AES.new(
                    session["password"],
                    AES.MODE_EAX,
                    nonce=row["nonce"],
                ).decrypt(row["password"])),
                row["id"],
                row["context"],
                row["username"]
            )
        session["password"] = new_pass
    return web.json_response({"success": True})


@authenticated
@required(username=str, password=str)
@optional(admin=bool)
async def create(request: web.Request) -> web.Response:
    """Create a new user.

    Required parameters:
    - username: string
    - password: string

    Optional parameters:
    - admin: boolean (default: false)
    """
    data = await request.json()

    session = await get_session(request)
    if not session["admin"]:
        raise web.HTTPForbidden(
            reason="Admin required",
            text=json.dumps(
                {
                    "success": False,
                    "msg": "Admin required",
                    "error_code": "admin_required",
                }
            )
        )
    salt = urandom(config.SALT_LENGTH)
    async with request.app["asynpg.pool"].acquire() as database:
        row = await database.fetchrow(
            "SELECT * FROM sessions WHERE username=$1",
            data["username"]
        )
        if row:
            raise web.HTTPBadRequest(
                reason=f"User {data['username']} exists",
                text=json.dumps(
                    {
                        "success": False,
                        "msg": f"User {data['username']} exists",
                        "error_code": "user_exists",
                    },
                )
            )
        await database.execute(
            "INSERT INTO sessions (username, password, salt, admin) VALUES "
            "($1, $2, $3, $4)",
            data["username"],
            pbkdf2_hmac(
                "sha256",
                bytes(request["password"], "utf8"),
                salt,
                config.HASH_ITERATIONS,
            ),
            salt,
            data.get("admin", False)
        )
    return web.json_response({"success": True})
