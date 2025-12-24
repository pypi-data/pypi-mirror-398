"""Data models for UniFi Network Controller entities."""

from pydantic import BaseModel


class NetworkDevice(BaseModel):
    """Model for a UniFi network device."""

    mac: str
    name: str | None = None
    type: str | None = None
    model: str | None = None
    state: int  # 1 for online, 0 for offline
    uptime: int | None = None
    ip: str | None = None
    version: str | None = None
    adoptable_when_upgraded: bool | None = None
    adopted: bool
    site_id: str
    disabled: bool | None = None
    port_table: list[dict] | None = None


class NetworkClient(BaseModel):
    """Model for a UniFi network client."""

    mac: str
    ip: str | None = None
    name: str | None = None
    hostname: str | None = None
    oui: str | None = None
    is_wired: bool
    uplink: dict | None = None
    site_id: str
    first_seen: int | None = None
    last_seen: int | None = None
    is_guest: bool | None = None
    user_id: str | None = None
    dev_id_override: str | None = None


class NetworkWLAN(BaseModel):
    """Model for a UniFi WLAN configuration."""

    _id: str
    name: str
    site_id: str
    wlan_id: str
    ssid: str
    security: str
    wpa3_support: bool | None = None
    enabled: bool
    hide_ssid: bool
    is_guest: bool | None = None
    dtim_mode: str | None = None
    dtim_na: int | None = None
    dtim_ng: int | None = None


class NetworkSite(BaseModel):
    """Model for a UniFi site."""

    _id: str
    name: str
    desc: str | None = None
    role: str | None = None
    site_id: str
    attr_no_delete: bool | None = None
    attr_hidden_id: str | None = None
