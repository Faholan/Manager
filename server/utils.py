"""Utility functions.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

import json
import typing as t
from inspect import getdoc

from aiohttp import web
from aiohttp_session import get_session

from . import config


def get_subroutes(path: str, app: web.Application):
    """Get the subroutes, their associated method, and a description."""
    return [{
        "path": route.get_info()["path"],
        "method": route.method,
        "description": get_description(route.handler),
        "optional": get_optional(route.handler),
        "required": get_required(route.handler),
        "authenticated": getattr(route.handler, "authenticated", False),
    } for route in app.router.routes()
        if route.get_info()["path"].startswith(path)]


def get_description(handler) -> t.Optional[str]:
    """Get a handler's description."""
    doc = getdoc(handler)
    if doc:
        doc = doc.split("\n", maxsplit=1)[0]
    return getattr(handler, "description", doc)


def get_optional(handler) -> t.Dict[str, str]:
    """Get a handler's optional arguments."""
    return {
        name: config.CLASS_NAMES.get(cls, cls.__name__)
        for name, cls in getattr(handler, "optional", {})
    }


def get_required(handler) -> t.Dict[str, str]:
    """Get a handler's required arguments."""
    return {
        name: config.CLASS_NAMES.get(cls, cls.__name__)
        for name, cls in getattr(handler, "required", {})
    }


def required(**fields: t.Type):
    """Require json data with specific field types."""
    def callback(handler):
        """Handle the function conversion."""
        async def check_and_run(request):
            try:
                data = await request.json()
            except json.JSONDecodeError:
                raise web.HTTPBadRequest(
                    reason="Malformed JSON data",
                    text=json.dumps({
                        "success": False,
                        "msg": "Malformed JSON data",
                        "error_code": "malformed_json",
                    }),
                )

            for name, datatype in fields.items():
                if name not in data:
                    raise web.HTTPBadRequest(
                        reason=f"Missing field {name}",
                        text=json.dumps({
                            "success": False,
                            "msg": f"Missing field {name}",
                            "error_code": "missing_field",
                        }),
                    )
                if not isinstance(data[name], datatype):
                    raise web.HTTPBadRequest(
                        reason=f"Field {name} must be of type {datatype}",
                        text=json.dumps({
                            "success": False,
                            "msg": f"Field {name} must be of type {datatype}",
                            "error_code": "wrong_field_type",
                        }),
                    )
            return await handler(request)

        for key, value in handler.__dict__.items():
            setattr(check_and_run, key, value)
        check_and_run.required = getattr(handler, "required", {}) | fields
        check_and_run.description = get_description(handler)
        return check_and_run

    return callback


def optional(**fields: t.Type):
    """Check for type of optional fields."""
    def callback(handler):
        """Handle the function conversion."""
        async def check_and_run(request):
            if await request.text() == "":
                return await handler(request)
            try:
                data = await request.json()
            except json.JSONDecodeError:
                raise web.HTTPBadRequest(
                    reason="Malformed JSON data",
                    text=json.dumps({
                        "success": False,
                        "msg": "Malformed JSON data",
                        "error_code": "malformed_json",
                    }),
                )

            for name, datatype in fields.items():
                if name in data and not isinstance(data[name], datatype):
                    raise web.HTTPBadRequest(
                        reason=f"Field {name} must be of type {datatype}",
                        text=json.dumps({
                            "success": False,
                            "msg": f"Field {name} must be of type {datatype}",
                            "error_code": "wrong_field_type",
                        }),
                    )
            return await handler(request)

        for key, value in handler.__dict__.items():
            setattr(check_and_run, key, value)
        check_and_run.optional = getattr(handler, "optional", {}) | fields
        check_and_run.description = get_description(handler)
        return check_and_run

    return callback


def authenticated(handler):
    """Require authentication to perform the action."""
    async def check_and_run(request):
        """Check the authentication and defer to handler."""
        session = await get_session(request)

        if (session.get("id", None) is None
                or session.get("remote", None) != request.remote):
            raise web.HTTPForbidden(
                reason="Authentication required",
                text=json.dumps(
                    {
                        "success": False,
                        "msg": "Authentication required",
                        "error_code": "auth_required",
                    }, ),
            )
        return await handler(request)

    check_and_run.authenticated = True
    for key, value in handler.__dict__.items():
        setattr(check_and_run, key, value)
    check_and_run.description = get_description(handler)
    return check_and_run
