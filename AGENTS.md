# AGENTS.md  
## Zerobyte Home Assistant Integration – Internal Architecture & Component Agents

This document describes the internal “agents” (modules, components, and logical units) that make up the Zerobyte Home Assistant integration.  
Each agent has a clear responsibility and communicates with others through well‑defined data structures.

---

# 🧩 1. API Agent (`api.py`)

### **Role**  
Handles all communication with the Zerobyte backend.

### **Responsibilities**
- Authentication (session-based login)
- Fetching:
  - Volumes + statfs
  - Repositories + detail + snapshots
  - Backups + detail
- Normalizing Zerobyte’s inconsistent API structures
- Converting timestamps to Python datetime
- Providing a clean, predictable data model to the Coordinator

### **Output Structure**
```python
{
  "volumes": [...],
  "repositories": [...],
  "backups": [...]
}
```

---

# 🔄 2. Coordinator Agent (`coordinator.py`)

### **Role**  
Central orchestrator for all Zerobyte data.

### **Responsibilities**
- Periodically calls the API Agent
- Merges all Zerobyte data into a unified structure
- Ensures sensors always receive fresh, consistent data
- Handles retry logic and error propagation
- Acts as the “single source of truth” for the integration

### **Behavior**
- Runs on a configurable interval
- Triggers entity updates automatically

---

# 📡 3. Sensor Agent (`sensor.py`)

### **Role**  
Transforms Zerobyte data into Home Assistant entities.

### **Design Philosophy**  
**One entity per Zerobyte object**, with all details stored in attributes.

### **Sensor Types**
#### Volume Sensor
- State: volume status  
- Attributes: total, used, free, backend, path  

#### Repository Sensor
- State: repository status  
- Attributes: snapshot count, last snapshot, compression stats  

#### Backup Sensor
- State: last backup status  
- Attributes: last run, next run, volume, repository, cron, retention  

### **Features**
- Dynamic MDI icons  
- Attribute‑based design  
- Automatic updates via Coordinator  

---

# 🧱 4. HACS Agent (`hacs.json`)

### **Role**  
Enables installation and updates through Home Assistant Community Store.

### **Responsibilities**
- Defines metadata for HACS  
- Ensures correct folder structure  
- Enables README rendering  

---

# 🧭 5. Integration Flow

```
Zerobyte API → API Agent → Coordinator Agent → Sensor Agent → HA UI
                                                   ↓
                                              Automation Agent
                                                   ↓
                                              Dashboard Agent
```

Each agent has a single responsibility, making the integration stable, predictable, and easy to maintain.

---

# 🏁 Summary

The Zerobyte integration is built around a clean, modular architecture:

| Agent | Responsibility |
|-------|----------------|
| API | Fetch & normalize Zerobyte data |
| Coordinator | Central orchestrator |
| Sensors | Expose data to HA |
| Automations | Smart alerts & monitoring |
| Dashboard | UI presentation |
| HACS | Distribution metadata |

This structure ensures the integration is:

- maintainable  
- scalable  
- easy to extend  
- easy to understand  
