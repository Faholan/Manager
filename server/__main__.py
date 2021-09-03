"""Launch the server.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

from aiohttp import web

from . import config
from .main import make_app

if __name__ == "__main__":
    web.run_app(make_app(), **config.AIOHTTP)
