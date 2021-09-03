"""Manage stored identifiers.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

import json
from os import urandom

from aiohttp import web
from aiohttp_session import get_session
from Cryptodome.Cipher import AES

from . import config
from .utils import authenticated, optional, required


@authenticated
@optional(context=str, username=str)
async def get(request: web.Request) -> web.Response:
    """Get identifiers, optionally filtered by context and username.

    Optional arguments:
    - context: string
    - username: string
    """
    session = await get_session(request)

    async with request.app["asyncpg.pool"].acquire() as database:
        if await request.text() != "":
            data = await request.json()
            if "context" in data:
                if "username" in data:
                    rows = await database.fetch(
                        "SELECT * FROM identifiers WHERE id=$1 AND context=$2 AND username=$3",
                        session["id"],
                        data["context"],
                        data["username"],
                    )
                else:
                    rows = await database.fetch(
                        "SELECT * FROM identifiers WHERE id=$1 AND context=$2",
                        session["id"],
                        data["context"],
                    )
            elif "username" in data:
                rows = await database.fetch(
                    "SELECT * FROM identifiers WHERE id=$1 AND username=$3",
                    session["id"],
                    data["username"],
                )
            else:
                rows = await database.fetch(
                    "SELECT * FROM identifiers WHERE id=$1",
                    session["id"],
                )
        else:
            rows = await database.fetch(
                "SELECT * FROM identifiers WHERE id=$1",
                session["id"],
            )
    return web.json_response({
        "success":
        True,
        "result": [{
            "context":
            row["context"],
            "username":
            row["username"],
            "password":
            AES.new(
                session["password"],
                AES.MODE_EAX,
                nonce=row["nonce"],
            ).decrypt(row["password"]),
        } for row in rows],
    })


@authenticated
@required(context=str, username=str, password=str)
async def insert(request: web.Request) -> web.Response:
    """Create a new record.

    Required arguments:
    - context: string
    - username: string
    - password: string
    """
    session = await get_session(request)
    data = await request.json()

    nonce = urandom(config.NONCE_LENGTH)

    async with request.app["asyncpg.pool"].acquire() as database:
        row = await database.fetchrow(
            "SELECT * FROM identifiers WHERE id=$1 AND context=$2 AND username=$3",
            session["id"],
            data["context"],
            data["username"],
        )
        if row:
            raise web.HTTPBadRequest(
                reason="Record already exists",
                text=json.dumps(
                    {
                        "success": False,
                        "msg": "Record already exists",
                        "error_code": "record_exists",
                    }, ),
            )
        await database.execute(
            "INSERT INTO identifiers VALUES ($1, 2, $3, $4, $5)",
            session["id"],
            data["context"],
            data["username"],
            AES.new(
                session["password"],
                AES.MODE_EAX,
                nonce=nonce,
            ).encrypt(data["password"]),
            nonce,
        )
    return web.json_response({"success": True})


@authenticated
@required(context=str, username=str, password=str)
async def update(request: web.Request) -> web.Response:
    """Update an existing record.

    Required arguments:
    - context: string
    - username: string
    - password: string
    """
    session = await get_session(request)
    data = await request.json()

    nonce = urandom(config.NONCE_LENGTH)

    async with request.app["asyncpg.pool"].acquire() as database:
        row = await database.fetchrow(
            "SELECT * FROM identifiers WHERE id=$1 AND context=$2 AND username=$3",
            session["id"],
            data["context"],
            data["username"],
        )
        if not row:
            raise web.HTTPBadRequest(
                reason="Record does not exist",
                text=json.dumps(
                    {
                        "success": False,
                        "msg": "Record does not exist",
                        "error_code": "unknown_record",
                    }, ),
            )
        await database.execute(
            "UPDATE identifiers SET password=$1, nonce=$2 WHERE "
            "id=$3 AND context=$4 AND username=$5",
            AES.new(
                session["password"],
                AES.MODE_EAX,
                nonce=nonce,
            ).encrypt(data["password"]),
            nonce,
            session["id"],
            data["context"],
            data["username"],
        )
    return web.json_response({"success": True})


@authenticated
@required(context=str, username=str, password=str)
async def upsert(request: web.Request) -> web.Response:
    """Insert a new record, or update it if it already exists.

    Required arguments:
    - context: string
    - username: string
    - password: string
    """
    session = await get_session(request)
    data = await request.json()

    nonce = urandom(config.NONCE_LENGTH)

    async with request.app["asyncpg.pool"].acquire() as database:
        await database.execute(
            "INSERT INTO identifiers VALUES ($1, 2, $3, $4, $5) "
            "ON CONFLICT (id, context, username) DO UPDATE SET password=$4 AND nonce=$5",
            session["id"],
            data["context"],
            data["username"],
            AES.new(
                session["password"],
                AES.MODE_EAX,
                nonce=nonce,
            ).encrypt(data["password"]),
            nonce,
        )
    return web.json_response({"success": True})


@authenticated
@required(context=str, username=str)
async def remove(request: web.Request) -> web.Response:
    """Remove a record.

    Required arguments:
    - context: string
    - username: string
    """
    session = await get_session(request)
    data = await request.json()

    async with request.app["asyncpg.pool"].acquire() as database:
        await database.execute(
            "DELETE FROM identifiers WHERE id=$1 AND context=$2 AND username=$3",
            session["id"],
            data["context"],
            data["username"],
        )
    return web.json_response({"success": True})
