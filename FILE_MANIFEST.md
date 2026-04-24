# VPD Control System v3.1.0 - File Manifest

## Package Contents

This package contains a complete VPD (Vapor Pressure Deficit) control system for mushroom cultivation chambers, built for Home Assistant.

---

## 📁 Documentation Files

### README.md
**Complete system documentation**
- System overview and features
- Architecture diagrams
- Hardware requirements
- Installation instructions
- Configuration guide
- Usage manual
- Troubleshooting
- Technical details
- Quick reference card

**Read this first!**

### SYSTEM_ARCHITECTURE.md
**Technical architecture documentation**
- System diagram (ASCII art)
- Data flow pipeline
- Control logic flowcharts
- Component interaction matrix
- State machine diagram

**For understanding how the system works internally**

### INSTALLATION_CHECKLIST.md
**Step-by-step installation checklist**
- Pre-installation verification
- File deployment steps
- Entity ID replacement
- Configuration merging
- Validation steps
- Post-installation verification

**Follow this during installation**

### CHANGELOG.md
**Version history and updates**
- v3.1.0: Fogger burst increased to 10s
- v3.0.0: Complete refactor with immortal triggers
- v2.0.0: VPD-based control
- v1.0.0: Initial release

**Review before upgrading from older versions**

### GRAFANA_SETUP_INSTRUCTIONS.md
**Grafana dashboard setup guide**
- Prerequisites
- Installation steps
- Dashboard import
- Troubleshooting
- Configuration details

**Optional: Only if using Grafana integration**

### FILE_MANIFEST.md
**This file - package contents overview**

---

## 🔧 Configuration Files

### automations_vpd_v3.yaml
**Home Assistant automations**
- VPD Control: Fogger Burst (10s every 2 min)
- VPD Control: Emergency Stop
- Ventilation: Time Pattern (every 5 min)
- VPD System: Auto-start on boot
- VPD System: Enable automations on system ON
- VPD Alerts: Mobile notifications (3x)
- Chamber: Maximum RH Safety

**⚠️ IMPORTANT:**
- Replace entity_ids before use:
  - `switch.luftfukter` → your fogger switch
  - `switch.hvit_vifte_switch` → your fan switch
- Append to existing automations.yaml (don't replace)

**Lines of code:** ~760
**Automations:** 10

### configuration_vpd_sensors.yaml
**Template sensors for VPD calculations**
- Chamber Avg Temp (average of 3 sensors)
- Chamber Avg Humidity (average of 3 sensors)
- Chamber Current VPD (calculated)
- Dynamic RH Setpoint (calculated)
- VPD Stability Score (0-100%)
- Climate Health Score (0-100%)
- Humidity Control Efficiency
- Humidifier Runtime Percent
- ACH Actual

**⚠️ IMPORTANT:**
- Replace entity_ids before use:
  - `sensor.temp_sensor_1/2/3` → your temp sensors
  - `sensor.humidity_sensor_1/2/3` → your humidity sensors
- Merge into existing configuration.yaml under `template:` section

**Lines of code:** ~300
**Sensors:** 12

### input_numbers_vpd.yaml
**VPD system parameters**
- target_vpd_pinning (0.15 kPa)
- target_vpd_fruiting (0.20 kPa)
- vpd_hysteresis (0.03 kPa)
- ventilation_on_duration_pinning (40s)
- ventilation_on_duration_fruiting (65s)

**Usage:**
- Copy to `/config/input_numbers_vpd.yaml`
- Add to configuration.yaml: `input_number: !include input_numbers_vpd.yaml`

**Lines of code:** ~50
**Parameters:** 5

### input_booleans_vpd.yaml
**VPD system toggles**
- ventilation_pulse_mode (System ON/OFF)
- pinning_phase (Pinning/Fruiting toggle)

**Usage:**
- Copy to `/config/input_booleans_vpd.yaml`
- Add to configuration.yaml: `input_boolean: !include input_booleans_vpd.yaml`

**Lines of code:** ~10
**Toggles:** 2

### scripts_vpd.yaml
**Helper scripts**
- vpd_enable_all_automations (manual enable button)
- vpd_force_restart (full system restart)

**Usage:**
- Merge into `/config/scripts.yaml`
- Or copy entire file if scripts.yaml is empty (`{}`)

**Lines of code:** ~55
**Scripts:** 2

---

## 🎨 Dashboard Files

### vpd_dashboard_split_screen_pro.yaml
**Lovelace dashboard configuration**
- Split-screen layout (controls left, status right)
- System ON/OFF toggle
- Pinning/Fruiting phase toggle
- VPD parameter settings
- Quick Actions buttons (Enable Auto, Force Restart, Test Equipment)
- Phase Comparison Table
- Smart Alerts Panel
- Automation Status Panel
- Grafana iframe (12h graphs)
- Equipment Status cards

**⚠️ IMPORTANT:**
- Replace entity_ids with your sensors/switches
- Update Grafana URL if different from `http://192.168.1.251:3000`
- Remove Grafana iframe section if not using Grafana

**Usage:**
- Import via Dashboard → Edit → Raw Configuration Editor
- Paste entire content

**Lines of code:** ~300
**Custom cards required:**
- Mushroom Cards (HACS)
- Card Mod (HACS, optional)

### grafana_vpd_dashboard.json
**Grafana dashboard configuration**
- Temperature & Humidity graph (dual-axis, 12h)
- VPD graph with target annotations (12h)
- Climate Health Score (area chart)
- VPD Stability Score (area chart)
- Current VPD stat panel
- Current Temp stat panel
- Current Humidity stat panel
- Climate Health stat panel

**Usage:**
- Import via Grafana UI: Dashboards → Import
- Select file → Choose Home Assistant data source
- Dashboard URL: `/d/vpd-monitoring/vpd-climate-monitoring`

**Lines of code:** ~450
**Panels:** 8

---

## 📊 File Statistics

| File Type | Count | Total Lines | Total Size |
|-----------|-------|-------------|------------|
| Documentation (MD) | 6 | ~2500 | ~150 KB |
| Configuration (YAML) | 6 | ~1200 | ~70 KB |
| Dashboard (YAML) | 1 | ~300 | ~15 KB |
| Grafana (JSON) | 1 | ~450 | ~15 KB |
| **TOTAL** | **14** | **~4450** | **~250 KB** |

---

## 🔄 Installation Order

**Recommended installation sequence:**

1. **Read Documentation:**
   - README.md (overview, requirements)
   - INSTALLATION_CHECKLIST.md (preparation)

2. **Prepare Files:**
   - Update entity_ids in all configuration files
   - Validate YAML syntax

3. **Deploy Configuration:**
   - input_numbers_vpd.yaml
   - input_booleans_vpd.yaml
   - configuration_vpd_sensors.yaml (merge)
   - automations_vpd_v3.yaml (append)
   - scripts_vpd.yaml (merge)

4. **Validate & Reload:**
   - Check Configuration
   - Reload all components

5. **Import Dashboard:**
   - vpd_dashboard_split_screen_pro.yaml

6. **Optional: Grafana:**
   - grafana_vpd_dashboard.json
   - GRAFANA_SETUP_INSTRUCTIONS.md

7. **Verify:**
   - INSTALLATION_CHECKLIST.md (post-install steps)

---

## 🛠️ Required Tools/Dependencies

### Home Assistant
- Version: 2023.1 or newer
- Supervisor/Container/Core installation

### HACS
- Mushroom Cards
- Card Mod (optional)
- ApexCharts Card (optional, if not using Grafana)

### Hardware
- 3x Temperature sensors (DHT22, BME280, etc.)
- 3x Humidity sensors (DHT22, BME280, etc.)
- 1x Fogger/Humidifier (smart plug controlled)
- 1x Extraction fan (smart plug controlled)

### Optional
- Grafana (for historical graphs)
- Mobile device with Home Assistant Companion App (for notifications)

---

## 📝 License & Credits

**License:** Personal and educational use

**Credits:**
- Developed for Home Assistant mushroom cultivation automation
- Uses standard Home Assistant components
- Mushroom Cards by @piitaya
- Card Mod by @thomasloven
- ApexCharts Card by @RomRider

---

## 🆘 Support

**For installation help:**
1. Read README.md → Installation section
2. Follow INSTALLATION_CHECKLIST.md step-by-step
3. Check README.md → Troubleshooting section
4. Review Home Assistant logs: Settings → System → Logs

**For technical details:**
- SYSTEM_ARCHITECTURE.md (system internals)
- CHANGELOG.md (version history, migration guides)

---

## 📦 Package Version

**Version:** 3.1.0
**Release Date:** 2025-12-17
**Package Format:** ZIP (Windows) / TAR.GZ (Linux/Mac)
**Compression:** DEFLATE / GZIP

---

## ✅ Integrity Check

**Expected file count:** 14 files
**Expected total size:** ~250 KB (uncompressed)

**Verify package integrity:**
```bash
# Count files
ls -1 | wc -l
# Should output: 14

# Check for required files
ls -1 | grep -E "(README|automations|configuration|dashboard)" | wc -l
# Should output: 4 or more
```

---

**End of File Manifest**

*For complete documentation, see README.md*
*For installation instructions, see INSTALLATION_CHECKLIST.md*
