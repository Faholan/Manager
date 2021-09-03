"""Copyright (C) 2021  Faholan <https://github.com/Faholan>."""

__author__ = "Faholan"
__license__ = "AGPL"
__copyright__ = "Copyright 2021 Faholan"
__version__ = "0.0.0a"

from typing import Literal, NamedTuple


class VersionInfo(NamedTuple):
    """Get information about the version."""

    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]


version_info = VersionInfo(major=0, minor=0, micro=0, releaselevel="alpha")
