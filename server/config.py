"""Configuration file.

Copyright (C) 2021  Faholan <https://github.com/Faholan>
"""

POSTGRESQL = {
    "user": "user",
    "password": "password",
    "database": "password_manager",
    "host": "127.0.0.1",
    "port": 5432,
}

COOKIE_NAME = "Faholan.Manager.storage"

HASH_ITERATIONS = 1000000

SALT_LENGTH = 32
NONCE_LENGTH = 16

CLASS_NAMES = {
    str: "string",
    int: "integer",
}

# aiohttp config

AIOHTTP = {
    "host": "0.0.0.0",
    "port": 8500,
}
