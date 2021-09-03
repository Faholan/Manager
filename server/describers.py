"""Static path description handling.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

from aiohttp import web

from . import __version__, version_info
from .utils import get_subroutes


async def root(request: web.Request) -> web.Response:
    """Serve information regarding this API."""
    return web.json_response(
        {
            "success": True,
            "description": "Self-hosted password manager",
            "version": __version__,
            "version_info": version_info._asdict(),
            "subroutes": get_subroutes("/", request.app),
        }
    )


async def user(request: web.Request) -> web.Response:
    """Serve information regarding the user route."""
    return web.json_response(
        {
            "success": True,
            "description": "Manage users",
            "subroutes": get_subroutes("/user", request.app),
        }
    )


async def identifiers(request: web.Request) -> web.Response:
    """Serve information regarding the identifiers route."""
    return web.json_response(
        {
            "success": True,
            "description": "Manage identifiers",
            "subroutes": get_subroutes("/identifiers", request.app),
        }
    )
