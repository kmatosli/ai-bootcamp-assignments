"""
schemas/common.py

Shared enums and base types used across all schemas.
"""
from enum import Enum


class DirectionEnum(str, Enum):
    long = "long"
    short = "short"
    watch = "watch"


class ConvictionEnum(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class StatusEnum(str, Enum):
    active = "active"
    closed = "closed"
    watchlist = "watchlist"


class RoleEnum(str, Enum):
    analyst = "analyst"
    pm = "pm"
    admin = "admin"
