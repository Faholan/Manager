"""Setup database.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

import asyncpg

from . import config


async def startup(app) -> None:
    """Create the database on startup."""
    app["asyncpg.pool"] = await asyncpg.create_pool(
        min_size=2,
        max_size=1000,
        **config.POSTGRESQL
    )


async def cleanup(app) -> None:
    """Cleanup the database connection."""
    await app["asyncpg.pool"].close()
