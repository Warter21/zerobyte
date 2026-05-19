📦 Zerobyte Home Assistant Integration

A custom Home Assistant integration for Zerobyte, a modern Restic‑based backup system.

This integration provides compact, attribute‑based sensors for Volumes, Repositories, and Backups.

Each Zerobyte entity appears as one HA sensor, with detailed information exposed via attributes.

✨ Features

✔ Volume Sensors

State: mounted, unmounted, error, etc.

Attributes:
- total (bytes)
- used (bytes)
- free (bytes)
- path
- backend

✔ Repository Sensors

State: healthy, error, etc.

Attributes:
- snapshots_count
- last_snapshot (ISO timestamp)
- compression_ratio
- compression_space_saving
- total_size
- uncompressed_size

✔ Backup Sensors

State: success, failed, running, etc.

Attributes:
- last_backup (ISO timestamp)
- next_backup (ISO timestamp)
- volume (name)
- repository (name)
- cron (cron expression)
- retention (policy object)

🛠 Installation

Copy the integration folder into: /config/custom_components/zerobyte/
Restart Home Assistant.

Go to:
Settings → Devices & Services → Add Integration → Zerobyte

Enter:
- Zerobyte host (e.g. http://192.168.0.10:4096)
- Username
- Password
- Update interval (seconds)
