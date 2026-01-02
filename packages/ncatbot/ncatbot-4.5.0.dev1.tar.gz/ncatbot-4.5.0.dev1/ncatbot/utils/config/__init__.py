"""Config package - exports the public configuration API."""

from .config import config, ncatbot_config

__all__ = [
    "ncatbot_config",
    "config",
    "configCONFIG_PATH",
]
