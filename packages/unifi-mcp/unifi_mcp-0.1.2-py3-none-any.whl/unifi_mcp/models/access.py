"""Data models for UniFi Access Controller entities."""

from datetime import datetime

from pydantic import BaseModel


class AccessPoint(BaseModel):
    """Model for a UniFi Access Point."""

    mac: str
    name: str | None = None
    model: str | None = None
    state: int  # 1 for online, 0 for offline
    firmware_version: str | None = None
    ip: str | None = None
    connected_at: int | None = None
    site_id: str
    floorplan_id: str | None = None


class AccessUser(BaseModel):
    """Model for a UniFi Access user."""

    user_id: str
    name: str
    description: str | None = None
    email: str | None = None
    phone: str | None = None
    key: str | None = None
    site_id: str
    created_time: int | None = None


class AccessLog(BaseModel):
    """Model for a UniFi Access log entry."""

    log_id: str
    user_id: str
    username: str | None = None
    door_id: str
    door_name: str | None = None
    timestamp: datetime
    success: bool
    site_id: str
    event_type: str | None = None


class AccessDoor(BaseModel):
    """Model for a UniFi Access door."""

    door_id: str
    name: str
    description: str | None = None
    site_id: str
    access_point_id: str | None = None
    relay_id: int | None = None
    lock_type: str | None = None
    enabled: bool
