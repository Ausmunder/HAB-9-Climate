# VPD Control System v3 - Installation Checklist

Use this checklist to ensure complete and correct installation.

---

## Pre-Installation

### ☐ 1. Hardware Verification

- [ ] 3x Temperature sensors installed and working
- [ ] 3x Humidity sensors installed and working
- [ ] Fogger/Humidifier connected to smart plug
- [ ] Extraction fan connected to smart plug
- [ ] All devices paired with Home Assistant
- [ ] All entity_ids documented

**Entity IDs to document:**
```
Temp Sensor 1: _______________
Temp Sensor 2: _______________
Temp Sensor 3: _______________
Humidity Sensor 1: _______________
Humidity Sensor 2: _______________
Humidity Sensor 3: _______________
Fogger Switch: _______________
Fan Switch: _______________
Grow Light (optional): _______________
```

### ☐ 2. Backup Existing Configuration

```bash
# Create backup directory
mkdir -p /config/backups/pre_vpd_v3

# Backup files
cp /config/automations.yaml /config/backups/pre_vpd_v3/
cp /config/configuration.yaml /config/backups/pre_vpd_v3/
cp /config/scripts.yaml /config/backups/pre_vpd_v3/
```

- [ ] Backup created
- [ ] Backup location: _______________

### ☐ 3. HACS Custom Cards

- [ ] HACS installed
- [ ] Mushroom Cards installed
  - HACS → Frontend → Explore → "Mushroom"
- [ ] Card Mod installed (optional, for styling)
  - HACS → Frontend → Explore → "card-mod"
- [ ] ApexCharts Card installed (if NOT using Grafana)
  - HACS → Frontend → Explore → "apexcharts-card"
- [ ] Home Assistant restarted after card installation

---

## Installation Steps

### ☐ 4. File Deployment

- [ ] Extract ZIP to temporary location
- [ ] Review all files in VPD_V3_SYSTEM package:
  - [ ] README.md
  - [ ] SYSTEM_ARCHITECTURE.md
  - [ ] CHANGELOG.md
  - [ ] INSTALLATION_CHECKLIST.md (this file)
  - [ ] automations_vpd_v3.yaml
  - [ ] configuration_vpd_sensors.yaml
  - [ ] input_numbers_vpd.yaml
  - [ ] input_booleans_vpd.yaml
  - [ ] scripts_vpd.yaml
  - [ ] vpd_dashboard_split_screen_pro.yaml
  - [ ] grafana_vpd_dashboard.json
  - [ ] GRAFANA_SETUP_INSTRUCTIONS.md

### ☐ 5. Update Entity IDs

**CRITICAL:** Replace placeholder entity_ids with your actual sensors.

- [ ] Edit `configuration_vpd_sensors.yaml`:
  - Replace `sensor.temp_sensor_1` → your temp sensor 1
  - Replace `sensor.temp_sensor_2` → your temp sensor 2
  - Replace `sensor.temp_sensor_3` → your temp sensor 3
  - Replace `sensor.humidity_sensor_1` → your humidity sensor 1
  - Replace `sensor.humidity_sensor_2` → your humidity sensor 2
  - Replace `sensor.humidity_sensor_3` → your humidity sensor 3

- [ ] Edit `automations_vpd_v3.yaml`:
  - Replace `switch.luftfukter` → your fogger switch
  - Replace `switch.hvit_vifte_switch` → your fan switch
  - Replace `light.fruktenkammer` → your grow light (if used)

- [ ] Edit `vpd_dashboard_split_screen_pro.yaml`:
  - Replace all placeholder entity_ids with your actual entities
  - Update Grafana URL if different from `http://192.168.1.251:3000`

### ☐ 6. Merge Configuration Files

**DO NOT overwrite existing files. Merge content carefully.**

#### 6.1 configuration.yaml

- [ ] Open your `/config/configuration.yaml`
- [ ] Add these includes (if not already present):
  ```yaml
  input_number: !include input_numbers_vpd.yaml
  input_boolean: !include input_booleans_vpd.yaml
  script: !include scripts.yaml
  ```
- [ ] Merge template sensors from `configuration_vpd_sensors.yaml`:
  - [ ] Copy all sensors under `template: - sensor:` section
  - [ ] If you have existing template sensors, append (don't replace)
- [ ] Save file

#### 6.2 automations.yaml

- [ ] Open your `/config/automations.yaml`
- [ ] Scroll to end of file
- [ ] Append all automations from `automations_vpd_v3.yaml`
  - **Automations to add:**
    - VPD System: Auto-start ved HASS oppstart
    - VPD System: Enable Critical Automations
    - VPD Control: Fogger Burst (Time Pattern)
    - VPD Control: Emergency Stop Fogger
    - Ventilation: Time Pattern (Udødelig)
    - Ventilation: Stop Pulse Cycle (VPD)
    - Chamber - Maximum RH Safety
    - VPD Alert: Critical VPD Mobile Notification
    - VPD Alert: Climate Health Critical
    - VPD Alert: Fogger Not Responding
- [ ] Save file

#### 6.3 scripts.yaml

- [ ] Copy `scripts_vpd.yaml` content to `/config/scripts.yaml`
  - [ ] If scripts.yaml is empty (`{}`), replace entire file
  - [ ] If scripts.yaml has existing scripts, append VPD scripts
- [ ] Save file

#### 6.4 Input Files

- [ ] Copy `input_numbers_vpd.yaml` → `/config/input_numbers_vpd.yaml`
- [ ] Copy `input_booleans_vpd.yaml` → `/config/input_booleans_vpd.yaml`

### ☐ 7. Validate Configuration

- [ ] Developer Tools → YAML → **CHECK CONFIGURATION**
- [ ] Fix any errors reported
- [ ] Check again until no errors

### ☐ 8. Reload Components

**Do NOT restart yet. Reload components individually first.**

- [ ] Developer Tools → YAML → **Template Entities** → Reload
- [ ] Developer Tools → YAML → **Automations** → Reload
- [ ] Developer Tools → YAML → **Scripts** → Reload
- [ ] Developer Tools → YAML → **Input Booleans** → Reload
- [ ] Developer Tools → YAML → **Input Numbers** → Reload

### ☐ 9. Verify Template Sensors

- [ ] Developer Tools → States → Search "chamber"
- [ ] Verify these sensors exist and have values:
  - [ ] `sensor.chamber_avg_temp`
  - [ ] `sensor.chamber_avg_humidity`
  - [ ] `sensor.chamber_current_vpd_2`
  - [ ] `sensor.dynamic_rh_setpoint`
  - [ ] `sensor.climate_health_score`
  - [ ] `sensor.vpd_stability_score`

**If sensors show "unknown" or "unavailable":**
- Check entity_ids in templates match your actual sensors
- Check sensors are reporting data
- Check template syntax for errors

### ☐ 10. Import Dashboard

- [ ] Go to Lovelace UI
- [ ] Click ⋮ → **Edit Dashboard**
- [ ] Click ⋮ → **Raw Configuration Editor**
- [ ] Paste content from `vpd_dashboard_split_screen_pro.yaml`
- [ ] Click **Save**
- [ ] Verify dashboard loads without errors

**If errors appear:**
- Check custom cards are installed (Mushroom, Card Mod)
- Check entity_ids in dashboard YAML match your sensors
- Check Grafana URL is correct (or remove iframe section if not using Grafana)

---

## Post-Installation

### ☐ 11. Enable VPD System

**Option A: Dashboard Button**
- [ ] Click "Enable Auto" button (green, Quick Actions panel)

**Option B: Service Call**
```yaml
service: script.vpd_enable_all_automations
```
- [ ] Run service call in Developer Tools

**Option C: Restart Home Assistant**
- [ ] Restart Home Assistant (auto-start will activate system after 45s)

### ☐ 12. Verify Automation Status

- [ ] Open VPD Dashboard
- [ ] Check "Automation Status" panel
- [ ] Verify all show "✅ Enabled":
  - [ ] Fogger Burst (v3)
  - [ ] Ventilation (Udødelig)
  - [ ] Emergency Stop
  - [ ] Auto-start

**If any show "❌ Disabled":**
- Click "Enable Auto" button again
- Or run `script.vpd_enable_all_automations`
- Or manually enable in Settings → Automations

### ☐ 13. Start VPD System

- [ ] Toggle "VPD SYSTEM" to ON (top-left of dashboard)
- [ ] Verify system started:
  - `input_boolean.ventilation_pulse_mode` = ON

### ☐ 14. Select Phase

- [ ] Toggle "PINNING" or "FRUITING" (top-center of dashboard)
  - **Pinning:** 15°C target, 0.15 kPa VPD, ACH 4
  - **Fruiting:** 18°C target, 0.20 kPa VPD, ACH 7

### ☐ 15. Monitor Initial Operation

**Wait 10 minutes, then check:**

- [ ] Fogger automation triggered at least once
  - Check: Automation Status → "Last: X minutes ago"
- [ ] Ventilation automation triggered at least once
  - Check: Automation Status → "Last: X minutes ago"
- [ ] VPD sensor updating
  - Check: Current value reasonable (0.10-0.40 kPa)
- [ ] Climate Health Score calculating
  - Check: Value between 0-100%
- [ ] No errors in logs
  - Settings → System → Logs → Filter by "vpd" or "automation"

### ☐ 16. Test Equipment Manually

- [ ] Click "Test Fogger" button → Fogger turns ON → Click again to turn OFF
- [ ] Click "Test Vifte" button → Fan turns ON → Click again to turn OFF
- [ ] Verify physical equipment responds

### ☐ 17. Calibrate Parameters (Optional)

**If needed, adjust these in dashboard Settings panel:**

- [ ] `target_vpd_pinning` - Adjust if VPD too high/low in pinning
- [ ] `target_vpd_fruiting` - Adjust if VPD too high/low in fruiting
- [ ] `vpd_hysteresis` - Increase if fogger cycling too much, decrease if VPD unstable
- [ ] `ventilation_on_duration_pinning` - Adjust for correct ACH
- [ ] `ventilation_on_duration_fruiting` - Adjust for correct ACH

---

## Optional: Grafana Integration

### ☐ 18. Grafana Setup (Optional)

**Only if you want historical graphs in dashboard:**

- [ ] Grafana installed on Home Assistant or separate server
- [ ] Home Assistant data source configured in Grafana
- [ ] Follow `GRAFANA_SETUP_INSTRUCTIONS.md`
- [ ] Import `grafana_vpd_dashboard.json`
- [ ] Verify Grafana dashboard URL accessible
- [ ] Update iframe URL in `vpd_dashboard_split_screen_pro.yaml` if needed

**If skipping Grafana:**
- [ ] Remove iframe section from dashboard YAML (lines ~286-290)
- [ ] Optional: Install ApexCharts Card and use ApexCharts graphs instead

---

## Mobile Notifications (Optional)

### ☐ 19. Configure Mobile App

- [ ] Home Assistant Companion App installed on phone
- [ ] Device name: _______________
- [ ] Update notification entity in automations:
  - Replace `notify.mobile_app_pixel_9a` with your device:
    - VPD Critical Alert (line ~692)
    - Climate Health Critical (line ~710)
    - Fogger Not Responding (line ~728)

---

## Final Verification

### ☐ 20. System Health Check

**After 24 hours of operation:**

- [ ] Climate Health Score > 50%
- [ ] VPD Stability Score > 50%
- [ ] VPD within target ±0.10 kPa
- [ ] RH within target ±5%
- [ ] Temperature stable (±2°C from target)
- [ ] No automation errors in logs
- [ ] Fogger runtime reasonable (check `sensor.humidifier_runtime_percent`)
- [ ] Equipment operating normally

### ☐ 21. Documentation

- [ ] Note current parameter values:
  ```
  target_vpd_pinning: _______
  target_vpd_fruiting: _______
  vpd_hysteresis: _______
  ventilation_on_duration_pinning: _______
  ventilation_on_duration_fruiting: _______
  ```
- [ ] Save configuration backup to safe location
- [ ] Bookmark README.md for future reference

---

## Troubleshooting

**If issues occur, see:**
- README.md → Troubleshooting section
- Settings → System → Logs
- Settings → Automations → [automation] → Traces

**Common issues:**
- Automations disabled → Click "Enable Auto" button
- VPD too high → Increase fogger burst or reduce hysteresis
- VPD too low → Decrease fogger burst or increase hysteresis
- RH unstable → Adjust ventilation duration or hysteresis

---

## ✅ Installation Complete!

**System should now be:**
- ✅ Monitoring VPD, temperature, humidity
- ✅ Automatically controlling fogger every 2 minutes
- ✅ Automatically ventilating every 5 minutes
- ✅ Providing safety emergency stop
- ✅ Auto-starting on Home Assistant boot
- ✅ Displaying comprehensive dashboard
- ✅ Sending mobile notifications (if configured)

**Next steps:**
- Monitor for 24-48 hours
- Adjust parameters as needed
- Enjoy automated mushroom cultivation! 🍄

---

**Installation Date:** _______________
**Installed By:** _______________
**Notes:**
_______________
_______________
_______________
