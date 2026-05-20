# Zerobyte Home Assistant Integration

A custom Home Assistant integration for Zerobyte, a modern Restic-based backup system.  
This integration provides compact, attribute-based sensors for Volumes, Repositories, and Backups.  
Each Zerobyte entity appears as one HA sensor, with detailed information exposed via attributes.

---

## 🚀 Features

- Volume sensors with storage metrics  
- Repository sensors with snapshot and compression data  
- Backup sensors with last/next run info  
- Dynamic MDI icons  
- Clean attribute-based design  
- Unified automation for monitoring and alerts  
- Optional Lovelace dashboard

---

## 📦 Installation

1. Copy the integration folder into:

```
/config/custom_components/zerobyte/
```

2. Restart Home Assistant  
3. Go to:  
   **Settings → Devices & Services → Add Integration → Zerobyte**

---

## 🔌 API Structure

The integration uses the Zerobyte API to fetch:

- Volumes  
- Repositories  
- Backups  
- Snapshot metadata  

All data is normalized into a clean Python structure before being exposed to Home Assistant.

---

## 🧩 Entities Overview

### **Volume Sensors**
- State: volume status  
- Attributes: total, used, free, backend, path  

### **Repository Sensors**
- State: repository status  
- Attributes: snapshot count, last snapshot, compression stats  

### **Backup Sensors**
- State: last backup status  
- Attributes: last run, next run, volume, repository, cron, retention  

---

## 📄 License

MIT License
