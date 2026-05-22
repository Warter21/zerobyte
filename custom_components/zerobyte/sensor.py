"""Zerobyte sensors (compact attribute-based version with icons)."""
from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    data = coordinator.data or {}

    # -----------------------------
    # VOLUMES
    # -----------------------------
    for vol in data.get("volumes", []):
        entities.append(ZerobyteVolumeSensor(coordinator, vol))

    # -----------------------------
    # REPOSITORIES
    # -----------------------------
    for repo in data.get("repositories", []):
        entities.append(ZerobyteRepositorySensor(coordinator, repo))

    # -----------------------------
    # BACKUPS
    # -----------------------------
    for backup in data.get("backups", []):
        entities.append(ZerobyteBackupSensor(coordinator, backup))

    async_add_entities(entities)


# ============================================================
# BASE CLASS
# ============================================================

class ZerobyteBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for compact Zerobyte sensors."""

    def __init__(self, coordinator, item):
        super().__init__(coordinator)
        self._item = item

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "zerobyte")},
            name="Zerobyte",
            manufacturer="Zerobyte",
        )

    def _find_item(self):
        data = self.coordinator.data or {}

        # volumes
        if "statfs" in self._item:
            for v in data.get("volumes", []):
                if v.get("name") == self._item.get("name"):
                    return v

        # repositories
        if "snapshots" in self._item:
            for r in data.get("repositories", []):
                if r.get("id") == self._item.get("id"):
                    return r

        # backups
        if "lastBackupAt" in self._item:
            for b in data.get("backups", []):
                if b.get("id") == self._item.get("id"):
                    return b

        return self._item


# ============================================================
# VOLUME SENSOR
# ============================================================

class ZerobyteVolumeSensor(ZerobyteBaseSensor):
    @property
    def name(self):
        return f"Zerobyte Volume – {self._item.get('name')}"

    @property
    def unique_id(self):
        return f"zerobyte_volume_{self._item.get('name')}"

    @property
    def icon(self):
        status = (self._find_item().get("status") or "").lower()
        if status == "mounted":
            return "mdi:harddisk"
        if status == "error":
            return "mdi:harddisk-alert"
        return "mdi:harddisk-off"

    @property
    def state(self):
        item = self._find_item()
        return item.get("status")

    @property
    def extra_state_attributes(self):
        item = self._find_item()
        stat = item.get("statfs", {})

        return {
            "total": stat.get("total"),
            "used": stat.get("used"),
            "free": stat.get("free"),
            "path": item.get("config", {}).get("path"),
            "backend": item.get("config", {}).get("backend"),
        }


# ============================================================
# REPOSITORY SENSOR
# ============================================================

class ZerobyteRepositorySensor(ZerobyteBaseSensor):
    @property
    def name(self):
        return f"Zerobyte Repository – {self._item.get('name')}"

    @property
    def unique_id(self):
        return f"zerobyte_repository_{self._item.get('id')}"

    @property
    def icon(self):
        status = (self._find_item().get("status") or "").lower()
        if status == "healthy":
            return "mdi:folder-sync"
        if status == "error":
            return "mdi:folder-alert"
        return "mdi:folder-sync-outline"

    @property
    def state(self):
        item = self._find_item()
        return item.get("status")

    @property
    def extra_state_attributes(self):
        item = self._find_item()
        stats = item.get("stats", {})
        snaps = item.get("snapshots", [])

        last_snap = None
        if snaps:
            ts = max(snaps, key=lambda s: s.get("time", 0)).get("time")
            if ts:
                if ts > 1e10:
                    ts = ts / 1000
                last_snap = datetime.fromtimestamp(ts).isoformat()

        return {
            "snapshots_count": len(snaps),
            "last_snapshot": last_snap,
            "compression_ratio": stats.get("compression_ratio"),
            "compression_space_saving": stats.get("compression_space_saving"),
            "total_size": stats.get("total_size"),
            "uncompressed_size": stats.get("total_uncompressed_size"),
        }


# ============================================================
# BACKUP SENSOR
# ============================================================

class ZerobyteBackupSensor(ZerobyteBaseSensor):
    @property
    def name(self):
        return f"Zerobyte Backup – {self._item.get('name')}"

    @property
    def unique_id(self):
        return f"zerobyte_backup_{self._item.get('id')}"

    @property
    def icon(self):
        status = (self._find_item().get("lastBackupStatus") or "").lower()
        if status == "success":
            return "mdi:check-circle"
        if status == "failed":
            return "mdi:alert-circle"
        if status == "running":
            return "mdi:progress-clock"
        return "mdi:backup-restore"

    @property
    def state(self):
        item = self._find_item()
        return item.get("lastBackupStatus")

    @property
    def extra_state_attributes(self):
        item = self._find_item()

        def fmt(ts):
            if not ts:
                return None
            if ts > 1e10:
                ts = ts / 1000
            return datetime.fromtimestamp(ts).isoformat()

        return {
            "last_backup": fmt(item.get("lastBackupAt")),
            "next_backup": fmt(item.get("nextBackupAt")),
            "volume": item.get("volume", {}).get("name"),
            "repository": item.get("repository", {}).get("name"),
            "cron": item.get("cronExpression"),
            "retention": item.get("retentionPolicy"),
        }
