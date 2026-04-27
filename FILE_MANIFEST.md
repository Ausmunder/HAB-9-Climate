# HAB-9 VPD Control System v2.0.0 - File Manifest

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

### automations.yaml
**Hjem-automasjoner + HAB-9 systemlivssyklus og varsler**
- System: startup, start, stop
- VPD-varsler: kritisk høy/lav VPD, fogger inaktiv, vifte inaktiv
- Fase-styring: pinning 48h auto-retur
- Anomali-deteksjon: temp/RH-endring, sensor offline, temp/RH utenfor område
- Daglig morgenrapport
- Hjem-automasjoner (varmepumpe, biler, personer)

### fogger.yaml *(ny i v2.0)*
**All fogger-logikk — VPD-first med safety overrides**
- `fogger_vpd_control` — Event-trigger på VPD state change (erstatter polling)
- `fogger_burst_end` — Auto-off etter `fogger_burst_duration` sekunder
- `fogger_blocked_by_fan_trigger` — Anti-oscillasjon 30s etter viftestart
- `fogger_adaptive_retrigger` — Rask retrigger ved VPD > target + 0.05 kPa
- `fogger_watchdog_safety` — Tvang-OFF etter 3 min (ned fra 10 min)
- `fogger_rh_hard_cutoff` — RH > 98% → fogger OFF umiddelbart (ingen conditions)

### ventilation.yaml *(ny i v2.0)*
**Ventilasjonssyklus — forenklet fra 4 automasjoner til 1**
- `ventilation_cycle_sequence` — Sekvens: burst1 → pause → burst2 → restart timer
- `ach_sync` — Restart syklus ved ACH- eller fan_total_on_time-endring
- `ventilation_timer_idle_watchdog` — Recovery ved 10 min idle timer
- `fan_watchdog_safety` — Tvang-OFF etter 90s kjøretid

### power_safety.yaml *(ny i v2.0)*
**Power-verifisering for vifte og fogger**
- `fan_power_failure` — Underpower → OFF + restart syklus
- `fan_overpower` — Overpower → OFF + varsling
- `fogger_power_failure` — Underpower → lockout + varsling
- `fogger_overpower` — Overpower → OFF + varsling
- `fogger_lockout_reset` — Lockout reset etter timer

### configuration_vpd_sensors.yaml
**Template-sensorer, statistikk og HA-integrasjoner**
- Chamber Avg Temp (2x Aqara T1, fallback: kammeret)
- Chamber Avg Humidity (2x Aqara T1 +3% kalibrering)
- Chamber Current VPD (Magnus-formel)
- Ventilation Status, VPD Control Status, VPD Alert Status
- Sensor Health Status
- Rate-of-change sensorer (temp/RH 5 min)
- Statistics sensorer (24h snitt, 3h std dev)
- VPD In Range binary sensor

### input_numbers_vpd.yaml
**Alle konfigurerbare parametere**
- VPD-mål: `target_vpd_pinning` (0.10), `target_vpd_fruiting` (0.12)
- `vpd_hysteresis` (0.01 kPa)
- ACH: `ach_target_pinning` (6), `ach_target_fruiting` (7)
- `fogger_burst_duration` (14s), `fan_total_on_time` (120s)
- Power-grenser: `fan_power_min/max`, `fogger_power_min/max`
- `power_check_delay` (5s), `fogger_lockout_time` (120s)

### input_booleans_vpd.yaml
**System-toggles**
- `system_enabled` — Master ON/OFF
- `pinning_phase` — Pinning/Fruiting fase-toggle
- `fogger_lockout` — Safety lockout (settes av power_safety)
- `fogger_blocked_by_fan` — Anti-oscillasjon (settes av fogger automation)

### timer_vpd.yaml
**Timere**
- `ventilation_cycle` — Ventilasjonssyklus-timer
- `fogger_burst` — Begrenser enkelt-burst til `fogger_burst_duration`
- `fogger_lockout_timer` — Teller ned lockout-perioden
- `pinning_phase_countdown` — 48h auto-retur fra pinning

### scripts_vpd.yaml
**Hjelpeskripter**
- `vpd_force_restart` — Full system restart

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

**Version:** 2.0.0
**Release Date:** 2026-04-27

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
