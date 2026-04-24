# VPD-home System Review Package
Generert: 2026-04-24 08:52
GitHub: https://github.com/Ausmunder/VPD-home

## Filer inkludert
- **README.md** — Systemdokumentasjon og oppsett
- **SYSTEM_ARCHITECTURE.md** — Detaljert arkitektur og dataflyt
- **CHANGELOG.md** — Endringshistorikk
- **configuration_vpd_sensors.yaml** — HA konfigurasjon: template-sensorer
- **automations_vpd_v3.yaml** — Alle HA-automationer
- **input_numbers_vpd.yaml** — Konfigurerbare parametere (VPD-mål, ACH, etc.)
- **input_booleans_vpd.yaml** — Systemtilstander (pulse_mode, pinning_phase)
- **timer_vpd.yaml** — Ventilasjonssyklus-timer

---

# README.md
> Systemdokumentasjon og oppsett

```markdown
# VPD Control System v3 - Complete Documentation

> **Mushroom Cultivation Climate Control System**
> Automatic VPD (Vapor Pressure Deficit), Temperature & Humidity Management
> Built for Home Assistant

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Hardware Requirements](#hardware-requirements)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)
10. [Technical Details](#technical-details)

---

## 🎯 System Overview

The VPD Control System v3 is a comprehensive climate control solution for mushroom cultivation chambers. It maintains optimal growing conditions by automatically controlling:

- **VPD (Vapor Pressure Deficit)**: Air drying power measurement (kPa)
- **Humidity**: Relative humidity percentage
- **Temperature**: Monitored (passive control)
- **Ventilation**: Fresh air exchange (ACH - Air Changes per Hour)

### Key Metrics

| Phase | Temperature | Target VPD | Target RH | ACH | Fan on-tid/syklus |
|-------|-------------|------------|-----------|-----|-------------------|
| **Pinning** | 15°C | 0.10 kPa | ~94% | 6 | 120s / 480s |
| **Fruiting** | 17°C | 0.12 kPa | ~93% | 7 | 120s / 394s |

> **ACH-definisjon:** 1 ACH = 120s faktisk viftetid. ACH n = viften kjører n ganger per time.
> OFF-tid = (3600/ACH) − 120s. Syklusen styres av `timer.ventilation_cycle`.

---

## ✨ Features

### Core Features

✅ **Dual-Phase Control**
- Pinning Phase (15°C, 0.10 kPa VPD, 60s ventilation)
- Fruiting Phase (17°C, 0.12 kPa VPD, 75s ventilation)
- One-click phase toggle
- 48-hour auto-return timer from pinning to fruiting

✅ **Timer-basert ventilasjon**
- `timer.ventilation_cycle` styrer syklusfrekvens
- ACH justeres via UI — OFF-tid beregnes automatisk: `(3600/ACH) − 120s`
- Fogger: 14s bursts (proaktiv burst etter ventilasjon også)
- Viften går alltid nøyaktig 120s per syklus (1 ACH = 1 luftskifte)

✅ **Smart Control Logic**
- Hysteresis-based VPD control (±0.02 kPa dead zone)
- Emergency stop hvis VPD faller for lavt
- Dynamic RH setpoint calculation basert på temperatur
- Proaktiv 14s fog-burst etter fan OFF (VPD ≥ target)

✅ **Trygg oppstart**
- `startup_sensor_availability_check`: sjekker alle Aqara-sensorer 85s etter boot — blokkerer VPD-systemet og varsler mobil hvis noen er offline
- `safety_fan_off_on_ha_start`: vifte + fogger AV ved boot, timer starter etter 90s (kun hvis sensorer OK)
- `input_boolean.ventilation_pulse_mode` restorer forrige tilstand automatisk

✅ **Professional Monitoring**
- Split-screen Mushroom dashboard with Grafana integration
- Climate Health Score (0-100%)
- VPD Stability Score (0-100%)
- Real-time equipment status
- Mobile push notifications for critical alerts

✅ **Safety Features**
- Emergency stop at 95% RH (condensation prevention)
- VPD emergency stop (prevents over-humidification)
- Equipment runtime tracking
- Fogger malfunction detection

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   SENSORS    │      │ AUTOMATIONS  │                │
│  ├──────────────┤      ├──────────────┤                │
│  │ Temp (x3)    │──┐   │ Fogger Burst │                │
│  │ Humidity (x3)│  │   │ Ventilation  │                │
│  │ VPD Calc     │  │   │ Emergency    │                │
│  │ Health Score │  │   │ Auto-start   │                │
│  └──────────────┘  │   └──────────────┘                │
│                    │            │                        │
│                    ▼            ▼                        │
│  ┌─────────────────────────────────────┐               │
│  │      CONTROL LOGIC ENGINE           │               │
│  │  • Dynamic RH Setpoint              │               │
│  │  • VPD Calculation                  │               │
│  │  • Hysteresis Control               │               │
│  │  • Phase Management                 │               │
│  └─────────────────────────────────────┘               │
│                    │                                     │
│                    ▼                                     │
│  ┌──────────────────────────────────────┐              │
│  │         HARDWARE CONTROL             │              │
│  ├──────────────────────────────────────┤              │
│  │  switch.luftfukter (Fogger)          │              │
│  │  switch.hvit_vifte_switch (Fan)      │              │
│  │  light.fruktenkammer (Light)         │              │
│  └──────────────────────────────────────┘              │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
           ┌──────────────────────────┐
           │   GRAFANA DASHBOARD      │
           │  • Real-time graphs      │
           │  • 12h history           │
           │  • Mobile notifications  │
           └──────────────────────────┘
```

### Automation Flow

```
BOOT → Auto-start (45s delay) → Enable Automations → Start System
                                          │
                                          ▼
        ┌─────────────────────────────────────────────┐
        │         TIME PATTERN TRIGGERS                │
        ├─────────────────────────────────────────────┤
        │                                              │
        │  Every 2 min:                Every 5 min:   │
        │  ┌─────────────┐              ┌──────────┐  │
        │  │ Check VPD   │              │ Ventilate│  │
        │  │  > target?  │              │ Chamber  │  │
        │  └──────┬──────┘              └──────────┘  │
        │         │ YES                                │
        │         ▼                                    │
        │  ┌─────────────┐                            │
        │  │ Fogger ON   │                            │
        │  │ 12 seconds  │                            │
        │  └─────────────┘                            │
        │         │                                    │
        │         ▼                                    │
        │  ┌─────────────┐                            │
        │  │Emergency    │                            │
        │  │Stop Monitor │                            │
        │  └─────────────┘                            │
        └─────────────────────────────────────────────┘
```

---

## 🔧 Hardware Requirements

### Required Equipment

1. **Chamber Temperature/Humidity Sensors** (2x Aqara Temperature and Humidity Sensor T1)
   - Entity IDs: `sensor.chamber_sensor_1_temperature`, `sensor.chamber_sensor_1_humidity`
   - Entity IDs: `sensor.chamber_sensor_2_temperature`, `sensor.chamber_sensor_2_humidity`
   - Connected via ZHA (Zigbee)

2. **Incubation Room Sensors** (2x Sonoff SNZB-02P, monitoring only)
   - Entity IDs: `sensor.incubation_sensor_1_temperature`, `sensor.incubation_sensor_1_humidity`
   - Entity IDs: `sensor.incubation_sensor_2_temperature`, `sensor.incubation_sensor_2_humidity`
   - Connected via ZHA (Zigbee)
   - Range: -10-60°C, ±0.2°C accuracy, ±2% RH

3. **Ultrasonic Fogger/Humidifier**
   - Entity ID: `switch.fogger_switch`
   - ZHA Zigbee smart plug controlled
   - Startup lag: 1-2 seconds (compensated in software)

4. **Extraction Fan**
   - Entity ID: `switch.vifter_switch`
   - ZHA Zigbee smart plug controlled
   - CFM based on chamber volume (calculate ACH)

5. **Grow Light** (optional)
   - Entity ID: `light.fruktenkammer`

### Recommended Specifications

- **Chamber Volume**: 0.5 - 2.0 m³
- **Fan CFM**: Calculate based on target ACH
  - Formula: `CFM = (Volume_m³ × 35.3147) × ACH / 60`
  - Example: 1 m³ chamber, 7 ACH = 4.1 CFM (~118 L/min)
- **Fogger Output**: 200-400 mL/hour
- **Network**: WiFi or Ethernet for Home Assistant connectivity

---

## 📦 Installation

### Step 1: File Structure

Extract all files to your Home Assistant configuration directory:

```
/config/
├── automations.yaml              # VPD automations (merge with existing)
├── configuration.yaml            # Template sensors (merge with existing)
├── input_numbers_vpd.yaml        # VPD parameters
├── input_booleans_vpd.yaml       # Phase toggles
├── timer_vpd.yaml                # Timers (legacy, not used in v3)
├── scripts.yaml                  # Helper scripts
├── vpd_dashboard_split_screen_pro.yaml  # Lovelace dashboard
└── grafana_vpd_dashboard.json    # Grafana dashboard config
```

### Step 2: Merge Configuration Files

**IMPORTANT:** Do NOT overwrite existing files. Merge content carefully.

#### 2.1 Edit `configuration.yaml`

Add these includes if not already present:

```yaml
# VPD Control System
input_number: !include input_numbers_vpd.yaml
input_boolean: !include input_booleans_vpd.yaml
timer: !include timer_vpd.yaml
script: !include scripts.yaml

# Template sensors (merge with existing template: section)
template:
  - sensor:
      - name: "Chamber Avg Temp"
        # ... (see full file)
      - name: "Chamber Avg Humidity"
        # ... (see full file)
      # ... (all VPD sensors)
```

#### 2.2 Merge `automations.yaml`

**Copy these automations:**
- `VPD System: Auto-start ved HASS oppstart`
- `VPD System: Enable Critical Automations`
- `VPD Control: Fogger Burst (Time Pattern)`
- `VPD Control: Emergency Stop Fogger`
- `Ventilation: Time Pattern (Udødelig)`
- `Ventilation: Stop Pulse Cycle (VPD)`
- `Chamber - Maximum RH Safety`
- `VPD Alert: Critical VPD Mobile Notification`
- `VPD Alert: Climate Health Critical`
- `VPD Alert: Fogger Not Responding`

**Append to existing automations.yaml** (do not replace entire file)

### Step 3: Install Dependencies

#### 3.1 Custom Cards (via HACS)

Install these custom Lovelace cards:

```
HACS → Frontend → Explore & Download Repositories

1. mushroom (Mushroom Cards)
2. lovelace-card-mod (Card Mod)
3. apexcharts-card (ApexCharts Card) - optional if using Grafana
```

Restart Home Assistant after installation.

#### 3.2 Grafana Setup (Optional but Recommended)

See `GRAFANA_SETUP_INSTRUCTIONS.md` for detailed setup.

### Step 4: Configure Entity IDs

**Edit all files** and replace placeholder entity IDs with your actual sensors:

```yaml
# REPLACE THESE:
sensor.temp_sensor_1        → your_temp_sensor_1
sensor.temp_sensor_2        → your_temp_sensor_2
sensor.temp_sensor_3        → your_temp_sensor_3
sensor.humidity_sensor_1    → your_humidity_sensor_1
sensor.humidity_sensor_2    → your_humidity_sensor_2
sensor.humidity_sensor_3    → your_humidity_sensor_3
switch.luftfukter           → your_fogger_switch
switch.hvit_vifte_switch    → your_fan_switch
light.fruktenkammer         → your_grow_light
```

**Files to update:**
- `configuration.yaml` (template sensors)
- `automations.yaml` (all VPD automations)
- `vpd_dashboard_split_screen_pro.yaml` (dashboard cards)

### Step 5: Validate & Reload

```bash
# Check configuration
Developer Tools → YAML → CHECK CONFIGURATION

# Reload components
Developer Tools → YAML →
  - Template Entities (reload)
  - Automations (reload)
  - Scripts (reload)
  - Input Booleans (reload)
  - Input Numbers (reload)
```

### Step 6: Import Dashboard

```
1. Go to Lovelace Dashboard
2. Click ⋮ → Edit Dashboard → Raw Configuration Editor
3. Paste content from vpd_dashboard_split_screen_pro.yaml
4. Save
```

### Step 7: Enable VPD System

**Option 1:** Dashboard Button
- Click "Enable Auto" (green button in Quick Actions)

**Option 2:** Manual Service Call
```yaml
service: script.vpd_enable_all_automations
```

**Option 3:** Restart Home Assistant
- Auto-start will activate system automatically after 45s

---

## ⚙️ Configuration

### VPD Parameters (input_numbers_vpd.yaml)

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `target_vpd_pinning` | 0.15 kPa | 0.10-0.30 | Target VPD for pinning phase |
| `target_vpd_fruiting` | 0.20 kPa | 0.15-0.35 | Target VPD for fruiting phase |
| `vpd_hysteresis` | 0.03 kPa | 0.01-0.10 | Dead zone to prevent rapid cycling |
| `ventilation_on_duration_pinning` | 40s | 10-60s | Fan runtime for pinning (ACH 4) |
| `ventilation_on_duration_fruiting` | 65s | 10-90s | Fan runtime for fruiting (ACH 7) |

### Adjusting Parameters

#### Increase Humidity
```yaml
# Option 1: Reduce hysteresis (fogger activates sooner)
vpd_hysteresis: 0.02  # from 0.03

# Option 2: Increase fogger burst (more moisture per cycle)
# Edit automations.yaml, line ~659
delay:
  seconds: 12  # from 10

# Option 3: Reduce ventilation duration (less moisture removal)
ventilation_on_duration_fruiting: 55  # from 65
```

#### Decrease Humidity
```yaml
# Option 1: Increase hysteresis (fogger less aggressive)
vpd_hysteresis: 0.04  # from 0.03

# Option 2: Decrease fogger burst
delay:
  seconds: 8  # from 10

# Option 3: Increase ventilation duration
ventilation_on_duration_fruiting: 75  # from 65
```

#### Adjust Ventilation Rate
```yaml
# Calculate required fan runtime for target ACH:
# Runtime (s) = (ACH × Volume_m³ × 58.9) / Fan_CFM

# Example: 1 m³ chamber, 7 ACH, 118 L/min fan
# Runtime = (7 × 1 × 58.9) / 118 ≈ 3.5 minutes per cycle
# With 5-min intervals: 3.5 min ON, 1.5 min OFF
```

---

## 📊 Usage

### Phase Selection

**Pinning Phase (15°C target)**
```
Toggle: input_boolean.pinning_phase = ON
- Target VPD: 0.15 kPa
- Target RH: ~95%
- Ventilation: 40s every 5 min (ACH ~4)
```

**Fruiting Phase (18°C target)**
```
Toggle: input_boolean.pinning_phase = OFF
- Target VPD: 0.20 kPa
- Target RH: ~90%
- Ventilation: 65s every 5 min (ACH ~7)
```

### System Control

**Start System**
```yaml
# Via dashboard: Click VPD SYSTEM toggle (top-left)
# Via service call:
service: input_boolean.turn_on
target:
  entity_id: input_boolean.ventilation_pulse_mode
```

**Stop System**
```yaml
# Via dashboard: Click VPD SYSTEM toggle (top-left)
# Via service call:
service: input_boolean.turn_off
target:
  entity_id: input_boolean.ventilation_pulse_mode
```

**Force Restart**
```yaml
# Via dashboard: Click "Force Restart" (red button)
# Via service call:
service: script.vpd_force_restart
```

**Enable Automations**
```yaml
# Via dashboard: Click "Enable Auto" (green button)
# Via service call:
service: script.vpd_enable_all_automations
```

### Dashboard Guide

```
┌─────────────────────────────────────────────────────────┐
│  [VPD SYSTEM: ON/OFF]  [PINNING/FRUITING]              │
├─────────────────┬───────────────────────────────────────┤
│ LEFT COLUMN     │ RIGHT COLUMN                          │
├─────────────────┼───────────────────────────────────────┤
│ • Settings      │ • Phase Comparison Table             │
│ • Quick Actions │ • Smart Alerts Panel                  │
│                 │ • Automation Status                   │
├─────────────────┴───────────────────────────────────────┤
│             GRAFANA DASHBOARD (12h graphs)              │
│  • Temperature & Humidity                               │
│  • VPD                                                   │
│  • Climate Health & VPD Stability                       │
├─────────────────────────────────────────────────────────┤
│             EQUIPMENT STATUS                             │
│  [Fogger Runtime] [CO2] [Temp] [Humidity]              │
└─────────────────────────────────────────────────────────┘
```

### Mobile Notifications

System sends push notifications for:

1. **VPD Critical** (>0.35 kPa for 15 min)
   - Check fogger water level
   - Check fogger power
   - Verify humidity sensors

2. **Climate Health Critical** (<30% for 30 min)
   - Check all sensors
   - Verify automations enabled
   - Check fogger/fan operation

3. **Fogger Not Responding** (VPD >0.30 kPa for 60 min)
   - Check fogger nozzle for clogs
   - Verify water level
   - Check power supply

---

## 🔍 Troubleshooting

### Automations Not Enabled After Restart

**Symptoms:**
- Automation Status Panel shows "Disabled"
- Fogger Burst: ❌ Disabled
- Emergency Stop: ❌ Disabled

**Solution:**
```yaml
# Click "Enable Auto" button in dashboard
# OR run service call:
service: script.vpd_enable_all_automations
```

**Root Cause:**
Automations were manually disabled in Home Assistant UI. The disabled state persists across restarts.

**Prevention:**
Auto-start automation (enabled by default) will re-enable them on every boot.

---

### Humidity Too Low / VPD Too High

**Symptoms:**
- RH consistently 2-5% below target
- VPD 0.05-0.10 kPa above target
- Frequent large drops after ventilation

**Diagnosis:**
1. Check fogger duty cycle: 10s / 120s = 8.3%
2. Check ventilation: Every 5 minutes
3. Chamber may be drying out faster than fogger compensates

**Solutions:**

**A. Increase Fogger Burst (Recommended)**
```yaml
# Edit automations.yaml, fogger burst automation
delay:
  seconds: 12  # from 10 (10% duty cycle)
```

**B. Reduce Hysteresis**
```yaml
# Edit input_numbers_vpd.yaml
vpd_hysteresis:
  initial: 0.02  # from 0.03
```

**C. Reduce Ventilation Duration**
```yaml
# Edit input_numbers_vpd.yaml
ventilation_on_duration_fruiting:
  initial: 55  # from 65 (reduces moisture removal)
```

**D. Check Fogger Hardware**
- Water level sufficient?
- Nozzle clogged?
- Fogger output rate acceptable? (200-400 mL/hour)

---

### Humidity Too High / VPD Too Low

**Symptoms:**
- RH consistently above 95%
- VPD below 0.10 kPa
- Emergency stop frequently triggered

**Solutions:**

**A. Decrease Fogger Burst**
```yaml
# Edit automations.yaml
delay:
  seconds: 8  # from 10 (6.7% duty cycle)
```

**B. Increase Ventilation Duration**
```yaml
# Edit input_numbers_vpd.yaml
ventilation_on_duration_fruiting:
  initial: 75  # from 65
```

**C. Increase Hysteresis**
```yaml
# Edit input_numbers_vpd.yaml
vpd_hysteresis:
  initial: 0.04  # from 0.03
```

---

### VPD Oscillating / Unstable

**Symptoms:**
- VPD swings ±0.10 kPa rapidly
- VPD Stability Score <50%
- Frequent fogger on/off cycles

**Root Cause:**
Hysteresis too small or temperature fluctuating

**Solutions:**

**A. Increase Hysteresis**
```yaml
vpd_hysteresis:
  initial: 0.04  # from 0.03 (larger dead zone)
```

**B. Stabilize Temperature**
- Add thermostat-controlled heater
- Insulate chamber
- Move away from cold walls/windows

**C. Reduce Fogger Burst**
```yaml
delay:
  seconds: 8  # from 10 (less aggressive)
```

---

### Temperature Out of Range

**Symptoms:**
- Pinning: Temp >16°C or <12°C
- Fruiting: Temp >20°C or <16°C

**Note:**
VPD system does NOT control temperature (passive monitoring only)

**Solutions:**
- Add thermostat-controlled heating element
- Add cooling (fan, AC, peltier cooler)
- Relocate chamber to temperature-stable environment
- Adjust target VPD based on actual temperature:
  ```yaml
  # Example: Fruiting at 17°C instead of 18°C
  # Lower target VPD slightly to compensate
  target_vpd_fruiting: 0.18  # from 0.20
  ```

---

### Grafana Dashboard Not Loading

**Symptoms:**
- iframe shows "Refused to connect"
- Dashboard blank or error

**Solutions:**

**A. Check Grafana Allow Embedding**
```ini
# /etc/grafana/grafana.ini
[security]
allow_embedding = true
```

**B. Verify URL Accessibility**
```bash
curl http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring
```

**C. Check Home Assistant iframe URL**
```yaml
# Should use kiosk mode:
url: 'http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring?orgId=1&refresh=30s&theme=dark&kiosk=tv'
```

**D. Import Dashboard**
- See `GRAFANA_SETUP_INSTRUCTIONS.md`
- Import `grafana_vpd_dashboard.json`

---

### Climate Health Score Low

**Symptoms:**
- Health Score <50%
- VPD/RH/Temp all appear normal

**Diagnosis:**
Check component scores individually:

```yaml
# VPD Stability Score
sensor.vpd_stability_score  # Should be >70%

# Humidity Control Efficiency
sensor.humidity_control_efficiency  # Should be >70%

# Temperature (implicit in Climate Health)
# Target: 15°C (pinning) or 18°C (fruiting)
# Acceptable: ±1°C
```

**Solutions:**

**If VPD Stability Low:**
- Increase hysteresis (reduce cycling)
- Stabilize temperature
- Check sensor calibration

**If Humidity Efficiency Low:**
- Adjust fogger duty cycle
- Check ventilation settings
- Verify target RH is achievable

**If Temperature Drift:**
- Add temperature control (heater/cooler)
- Insulate chamber
- See "Temperature Out of Range" above

---

## 🛠️ Maintenance

### Daily Checks

- [ ] Climate Health Score >70%
- [ ] VPD within target ±0.05 kPa
- [ ] RH within target ±3%
- [ ] No automation errors in logs

### Weekly Maintenance

- [ ] Clean fogger nozzle (distilled water)
- [ ] Refill fogger reservoir
- [ ] Clean fan filter/blades
- [ ] Verify sensor readings (compare 3 sensors)
- [ ] Check automation status panel (all enabled)

### Monthly Maintenance

- [ ] Calibrate humidity sensors (salt test)
- [ ] Deep clean fogger (vinegar soak)
- [ ] Inspect wiring and connections
- [ ] Review logs for errors/warnings
- [ ] Backup configuration files

### Sensor Calibration

**Humidity Sensor Salt Test:**

1. Create saturated salt solution (NaCl + water)
2. Place in sealed container with humidity sensor
3. Wait 24 hours
4. Reading should stabilize at 75.5% RH (at 20°C)
5. Calculate offset: `offset = 75.5 - actual_reading`
6. Apply offset in Home Assistant sensor config

**Temperature Sensor Verification:**

1. Use calibrated thermometer as reference
2. Compare readings at room temp (20-25°C)
3. Offset should be <±0.5°C
4. If >±1°C, replace sensor

---

## 📐 Technical Details

### VPD Calculation

```python
# Saturation Vapor Pressure (SVP) - Magnus formula
SVP = 0.61078 * exp((17.27 * T) / (T + 237.3))  # kPa

# Actual Vapor Pressure
AVP = SVP * (RH / 100)

# Vapor Pressure Deficit
VPD = SVP - AVP = SVP * (1 - RH/100)
```

**Where:**
- `T` = Temperature (°C)
- `RH` = Relative Humidity (%)
- `VPD` = Vapor Pressure Deficit (kPa)

### Dynamic RH Setpoint

```python
# Calculate required RH for target VPD at current temp
target_RH = (1 - (target_VPD / SVP)) * 100

# Example: 18°C, target VPD 0.20 kPa
# SVP = 2.064 kPa
# target_RH = (1 - (0.20 / 2.064)) * 100 = 90.3%
```

### Hysteresis Control

```python
# Fogger activates when:
if VPD > (target_VPD + hysteresis):
    fogger_on()

# Fogger stops when:
if VPD < (target_VPD - hysteresis):
    fogger_off()

# Dead zone: 2 × hysteresis
# Example: hysteresis = 0.03 kPa
# Fogger ON: VPD > 0.23 kPa (0.20 + 0.03)
# Fogger OFF: VPD < 0.17 kPa (0.20 - 0.03)
# Dead zone: 0.17 - 0.23 kPa (0.06 kPa range)
```

### ACH Calculation

```python
# ACH-definisjon (v3.7+): 1 ACH = 120s fan on-tid
# ACH n = viften kjører n ganger per time
# OFF-tid = (3600 / ACH) - 120s
# Sykluslengde = 3600 / ACH

# Eksempel: ACH 7 (fruiting)
# Sykluslengde = 3600 / 7 ≈ 514s
# ON-tid = 120s, OFF-tid = 514 - 120 = 394s

# Duty cycle = 120 / (3600 / ACH) * 100
# Eksempel ACH 7: 120 / 514 * 100 ≈ 23.3%
```

### Climate Health Score

```python
# Component Scores (0-100%)
vpd_score = vpd_stability_score
rh_score = humidity_control_efficiency
temp_score = 100 - (|actual_temp - target_temp| × 20)
temp_score = max(0, min(100, temp_score))

# Weighted Average
climate_health = (vpd_score × 0.4) + (rh_score × 0.4) + (temp_score × 0.2)

# Thresholds:
# >70% = Excellent (green)
# 40-70% = Acceptable (orange)
# <40% = Critical (red)
```

### Entity ID Reference

**Sensors:**
- `sensor.chamber_avg_temp` - Average of 2 chamber temp sensors (Aqara T1)
- `sensor.chamber_avg_humidity` - Average of 2 chamber humidity sensors (Aqara T1)
- `sensor.chamber_current_vpd` - Calculated VPD from avg temp/humidity (kPa)
- `sensor.incubation_avg_temp` - Average of 2 incubation temp sensors (Sonoff SNZB-02P)
- `sensor.incubation_avg_humidity` - Average of 2 incubation humidity sensors (Sonoff SNZB-02P)
- `sensor.dynamic_rh_setpoint` - Target RH based on temp & phase
- `sensor.vpd_stability_score` - VPD stability (0-100%)
- `sensor.climate_health_score` - Overall health (0-100%)
- `sensor.humidity_control_efficiency` - RH control efficiency
- `sensor.humidifier_runtime_percent` - Fogger runtime estimate

**Controls:**
- `input_boolean.ventilation_pulse_mode` - System ON/OFF
- `input_boolean.pinning_phase` - Phase toggle
- `input_number.target_vpd_pinning` - Target VPD pinning
- `input_number.target_vpd_fruiting` - Target VPD fruiting
- `input_number.vpd_hysteresis` - Hysteresis (kPa)
- `input_number.ach_target_pinning` - ACH pinning (frekvens)
- `input_number.ach_target_fruiting` - ACH fruiting (frekvens)
- `input_number.ventilation_on_duration_pinning` - Fan on-tid pinning (fast: 120s)
- `input_number.ventilation_on_duration_fruiting` - Fan on-tid fruiting (fast: 120s)
- `timer.ventilation_cycle` - Aktiv nedtelling til neste syklus

**Switches:**
- `switch.fogger_switch` - Fogger (ZHA Zigbee)
- `switch.vifter_switch` - Extraction fan (ZHA Zigbee)
- `light.fruktenkammer` - Grow light

**Automations:**
- `automation.vpd_control_fogger_burst_v3` - Fogger 14s bursts (VPD > target, fail-safe off ved unavailable)
- `automation.vpd_control__emergency_stop_v3` - Emergency stop
- `automation.ventilation_timer_v4` - Timer-basert ventilasjon (primær syklusdrift)
- `automation.vpd_control_fog_after_ventilation` - Proaktiv fog-burst etter fan OFF
- `automation.fan_watchdog_safety` - **Lag 1**: Fan stuck ON >150s → turn off + restart timer
- `automation.ventilation_timer_idle_watchdog` - **Lag 3**: Timer idle >30 min → restart + push-varsling
- `automation.safety_fan_off_on_ha_start` - Fan+fogger AV ved boot, timer-start etter 90s
- `automation.startup_sensor_availability_check` - Blokkerer VPD-system og varsler mobil hvis sensorer offline 85s etter boot

---

## 📞 Support

### Getting Help

1. **Check logs:** Developer Tools → Logs (filter by "vpd" or "automation")
2. **Verify configuration:** Developer Tools → YAML → Check Configuration
3. **Review automation traces:** Settings → Automations → [automation] → Traces

### Common Log Errors

**"Entity not found: automation.vpd_..."**
- Solution: Use correct entity_id (based on automation `id:` field, not `alias:`)
- Example: `automation.vpd_control_fogger_burst_v3` (not `...time_pattern`)

**"Template error: unavailable"**
- Solution: Check sensor entity_ids exist and are not unavailable
- Verify sensors in: Settings → Devices & Services → Entities

**"Service not found: automation.turn_on"**
- Solution: Use `homeassistant.turn_on` to re-enable disabled automations

---

## 📄 License

This VPD Control System is provided as-is for personal and educational use in mushroom cultivation.

**Credits:**
- Developed for Home Assistant mushroom cultivation automation
- Uses standard Home Assistant components and community custom cards
- Grafana integration optional

---

## 🔄 Version History

**v3.7.2 (Current - 2026-04-20)**
- **Sensor-sjekk ved oppstart:** ny automation blokkerer VPD-system og varsler mobil hvis sensorer offline etter boot
- **Kritisk bugfix — fogger-loop:** unavailable VPD ga fallback 9.99 kPa → fogger fyrte hvert minutt. Nå: fail-safe off
- **safety_fan_off_on_ha_start:** delay 60s → 90s, slår nå også av fogger ved boot

**v3.7.1 (2026-04-19)**
- **Chamber sensors:** Byttet Sonoff SNZB-02WD → Aqara Temperature and Humidity Sensor T1
- **Fikset humidity-avg:** `chamber_avg_humidity` bruker nå `chamber_sensor_1/2_humidity` (ikke Netatmo)
- **Fikset sensor_health_status:** fjernet legacy `kammeret_humidity`-referanse

**v3.7.0 (2026-04-09)**
- **Ny ACH-definisjon:** 1 ACH = 120s fan on-tid. ACH n = n luftskifter/time
- **Timer-basert ventilasjon:** `timer.ventilation_cycle` erstatter `time_pattern`-trigger
- **ACH-aware inaktivitetsalert:** fan-alert basert på dynamisk forventet off-tid
- **Fjernet startupkonflikter:** 3 oppstartsautomater → 1 (`safety_fan_off_on_ha_start`)
- **Fjernet enable/disable-mekanisme:** erstattet av `ventilation_pulse_mode`-conditions
- **Koblet fogger til input_numbers:** UI-justering av VPD-mål har nå effekt
- **Sensor-rename:** `sensor.sensor_incubation_sensor_1_*` → `sensor.incubation_sensor_1_*`
- **Watchdog:** økt til 150s (var 120s = lik on-tid → utløste hvert syklus)
- **Dashboard:** `data.config.views`-struktur (ikke `data.views`), ventilasjonsstatus-seksjon

**v3.6.0 (2026-02-23)**
- Fogger burst økt til 14s, VPD-hysteresis redusert til 0.02 kPa
- Ny: Fog After Ventilation — 14s proaktiv burst etter fan OFF
- ZHA humidity kalibrering: +8.5% på chamber_sensor_1 og chamber_sensor_2

**v3.4.0 (2026-02-14)**
- **Replaced Netatmo sensors with 2x Sonoff SNZB-02WD** in fruiting chamber (ZHA Zigbee) → later replaced with 2x Aqara T1
- **Added 2x Sonoff SNZB-02P** in incubation room (monitoring only)
- **Removed ESPHome VPD dependency** - VPD now calculated from template sensor
- True dual-sensor averaging with graceful single-sensor fallback
- Incubation room dashboard section with 12h graphs
- Updated sensor health monitoring for all 4 new sensors

**v3.3.0 (2026-02-13)**
- Increased fogger burst from 10s to 12s (20% duty cycle) - improved humidity control
- Reduced fruiting ACH from 8 to 7 - better humidity retention
- Optimized VPD targets: Pinning 0.10 kPa, Fruiting 0.12 kPa

**v3.0**
- Increased fogger burst from 7s to 10s (8.3% duty cycle)
- Immortal time-pattern triggers (clock-based)
- Auto-start automation with retry logic
- Complete decoupling of fogger and ventilation
- Grafana dashboard integration
- Mobile push notifications
- Helper scripts for system management

**v2.0**
- Dynamic RH setpoint calculation
- Dual-phase control (pinning/fruiting)
- VPD-based hysteresis control
- Climate Health Score

**v1.0**
- Basic RH threshold control
- Timer-based automation
- Single-phase operation

---

## 📊 Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║            VPD CONTROL SYSTEM v3.7.0                   ║
║                QUICK REFERENCE                         ║
╠════════════════════════════════════════════════════════╣
║ PHASE          │ PINNING         │ FRUITING            ║
║────────────────┼─────────────────┼─────────────────────║
║ Temperature    │ 15°C            │ 17°C                ║
║ Target VPD     │ 0.10 kPa        │ 0.12 kPa            ║
║ Target RH      │ ~94%            │ ~93%                ║
║ Fan ON-tid     │ 120s            │ 120s                ║
║ Sykluslengde   │ ~600s (10 min)  │ ~514s (8.6 min)     ║
║ ACH            │ 6               │ 7                   ║
╠════════════════════════════════════════════════════════╣
║ FOGGER PARAMETERS                                      ║
║────────────────────────────────────────────────────────║
║ Burst Duration │ 14 seconds                            ║
║ Trigger        │ VPD ≥ target + hysteresis (0.02 kPa) ║
║ Proaktiv burst │ 14s etter fan OFF (VPD ≥ target)      ║
║ Emergency Stop │ RH > 98% or VPD normalized            ║
╠════════════════════════════════════════════════════════╣
║ SYSTEM CONTROL                                         ║
║────────────────────────────────────────────────────────║
║ Start System   │ Toggle "VPD SYSTEM" ON                ║
║ Stop System    │ Toggle "VPD SYSTEM" OFF               ║
║ Change Phase   │ Toggle "PINNING/FRUITING"             ║
║ Juster ACH     │ input_number.ach_target_fruiting      ║
╠════════════════════════════════════════════════════════╣
║ TROUBLESHOOTING                                        ║
║────────────────────────────────────────────────────────║
║ RH too low?    │ Increase fogger burst to 12s          ║
║ RH too high?   │ Decrease fogger burst to 8s           ║
║ VPD unstable?  │ Increase hysteresis to 0.04 kPa       ║
║ Auto disabled? │ Click "Enable Auto" button            ║
╠════════════════════════════════════════════════════════╣
║ MAINTENANCE SCHEDULE                                   ║
║────────────────────────────────────────────────────────║
║ Daily          │ Check Climate Health Score            ║
║ Weekly         │ Clean fogger, refill water            ║
║ Monthly        │ Calibrate sensors, backup config      ║
╚════════════════════════════════════════════════════════╝
```

---

**End of README**

For Grafana setup instructions, see `GRAFANA_SETUP_INSTRUCTIONS.md`
For system architecture diagram, see `SYSTEM_ARCHITECTURE.md`
For automation flowchart, see `AUTOMATION_FLOW.md`

```

---

# SYSTEM_ARCHITECTURE.md
> Detaljert arkitektur og dataflyt

```markdown
# VPD Control System v3 - System Architecture

## System Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                           MUSHROOM CULTIVATION CHAMBER                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  [Temp Sensors x3]  [Humidity Sensors x3]  [Mushroom Substrate]        │  │
│  │         │                    │                        ▲                  │  │
│  │         │                    │                        │                  │  │
│  │         └────────┬───────────┘              ┌─────────┴─────────┐       │  │
│  │                  │                          │  Ultrasonic Fogger │       │  │
│  │                  │                          │   (switch.luftfukter)      │  │
│  │                  │                          └─────────┬─────────┘       │  │
│  │         ┌────────▼──────────┐                         │                  │  │
│  │         │  Extraction Fan    │◄────────────────────────┘                 │  │
│  │         │ (hvit_vifte_switch)│                                          │  │
│  │         └────────────────────┘                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬────────────────────────────────────────────┘
                                   │
                                   │ WiFi/Ethernet
                                   │
┌──────────────────────────────────▼────────────────────────────────────────────┐
│                             HOME ASSISTANT SERVER                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         DATA COLLECTION LAYER                            │  │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │  │
│  │  │ Temp Sensor 1 │  │ Humidity Sen 1│  │ Equipment     │               │  │
│  │  │ Temp Sensor 2 │  │ Humidity Sen 2│  │ State Tracker │               │  │
│  │  │ Temp Sensor 3 │  │ Humidity Sen 3│  │ (switches)    │               │  │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘               │  │
│  │          │                   │                   │                        │  │
│  │          └───────────────────┼───────────────────┘                        │  │
│  │                              │                                            │  │
│  └──────────────────────────────┼────────────────────────────────────────────┘  │
│                                 │                                               │
│  ┌──────────────────────────────▼────────────────────────────────────────────┐ │
│  │                      TEMPLATE SENSOR LAYER                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Averaging & Calculations                                           │  │ │
│  │  │  ┌────────────────────┐  ┌────────────────────┐                     │  │ │
│  │  │  │ Chamber Avg Temp   │  │ Chamber Avg Humidity│                    │  │ │
│  │  │  │ (mean of 3 sensors)│  │ (mean of 3 sensors) │                    │  │ │
│  │  │  └─────────┬──────────┘  └──────────┬─────────┘                     │  │ │
│  │  │            └──────────────────┬──────┘                               │  │ │
│  │  │                               ▼                                      │  │ │
│  │  │              ┌────────────────────────────────┐                      │  │ │
│  │  │              │  Chamber Current VPD (v2)      │                      │  │ │
│  │  │              │  VPD = SVP × (1 - RH/100)      │                      │  │ │
│  │  │              │  SVP = 0.61078 × e^(...T...)   │                      │  │ │
│  │  │              └────────────┬───────────────────┘                      │  │ │
│  │  │                           │                                          │  │ │
│  │  └───────────────────────────┼──────────────────────────────────────────┘  │ │
│  │                              │                                             │ │
│  │  ┌───────────────────────────▼──────────────────────────────────────────┐  │ │
│  │  │  Dynamic Setpoint Calculation                                        │  │ │
│  │  │  ┌──────────────────────────────────────────────────────────────┐   │  │ │
│  │  │  │ Dynamic RH Setpoint                                          │   │  │ │
│  │  │  │ target_RH = (1 - target_VPD/SVP) × 100                       │   │  │ │
│  │  │  │                                                                │   │  │ │
│  │  │  │ Input: Pinning/Fruiting phase toggle                         │   │  │ │
│  │  │  │ Output: Dynamic RH target (adjusts for temperature)          │   │  │ │
│  │  │  └──────────────────────────────────────────────────────────────┘   │  │ │
│  │  └──────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                             │ │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Health & Performance Metrics                                        │  │ │
│  │  │  ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │  │ │
│  │  │  │ VPD Stability     │  │ Humidity Control │  │ Climate Health  │  │  │ │
│  │  │  │ Score (0-100%)    │  │ Efficiency       │  │ Score (0-100%)  │  │  │ │
│  │  │  │                   │  │ (0-100%)         │  │                 │  │  │ │
│  │  │  │ Deviation from    │  │ Deviation from   │  │ Weighted avg:   │  │  │ │
│  │  │  │ target VPD        │  │ target RH        │  │ 40% VPD + 40% RH│  │  │ │
│  │  │  │                   │  │                  │  │ + 20% Temp      │  │  │ │
│  │  │  └───────────────────┘  └──────────────────┘  └─────────────────┘  │  │ │
│  │  └──────────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         AUTOMATION CONTROL LAYER                         │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │   │
│  │  │  TIME PATTERN TRIGGERS (Immortal - Clock-Based)                   │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌─────────────────────────────────────────────────────────────┐  │   │   │
│  │  │  │  Every 2 Minutes (/2)                                        │  │   │   │
│  │  │  │  ┌────────────────────────────────────────────────────────┐ │  │   │   │
│  │  │  │  │  VPD Control: Fogger Burst (v3)                        │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  Condition:                                            │ │  │   │   │
│  │  │  │  │  ├─ System ON (ventilation_pulse_mode)                │ │  │   │   │
│  │  │  │  │  └─ VPD > (target_VPD + hysteresis)                    │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  Action:                                               │ │  │   │   │
│  │  │  │  │  ├─ Turn ON fogger (switch.luftfukter)                 │ │  │   │   │
│  │  │  │  │  ├─ Wait 10 seconds                                    │ │  │   │   │
│  │  │  │  │  └─ Turn OFF fogger                                    │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  Duty Cycle: 10s / 120s = 8.3%                         │ │  │   │   │
│  │  │  │  └────────────────────────────────────────────────────────┘ │  │   │   │
│  │  │  └─────────────────────────────────────────────────────────────┘  │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌─────────────────────────────────────────────────────────────┐  │   │   │
│  │  │  │  Every 5 Minutes (/5)                                        │  │   │   │
│  │  │  │  ┌────────────────────────────────────────────────────────┐ │  │   │   │
│  │  │  │  │  Ventilation: Time Pattern (Udødelig)                  │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  Condition:                                            │ │  │   │   │
│  │  │  │  │  └─ System ON (ventilation_pulse_mode)                 │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  Action:                                               │ │  │   │   │
│  │  │  │  │  ├─ Turn ON fan (hvit_vifte_switch)                    │ │  │   │   │
│  │  │  │  │  ├─ Wait (pinning: 40s, fruiting: 65s)                 │ │  │   │   │
│  │  │  │  │  └─ Turn OFF fan                                       │ │  │   │   │
│  │  │  │  │                                                         │ │  │   │   │
│  │  │  │  │  ACH: Pinning ~4, Fruiting ~7                          │ │  │   │   │
│  │  │  │  └────────────────────────────────────────────────────────┘ │  │   │   │
│  │  │  └─────────────────────────────────────────────────────────────┘  │   │   │
│  │  └───────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                           │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │   │
│  │  │  EVENT TRIGGERS (Safety & Monitoring)                             │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌────────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │  VPD Control: Emergency Stop                               │   │   │   │
│  │  │  │                                                             │   │   │   │
│  │  │  │  Trigger: VPD < (target - hysteresis) for 30s              │   │   │   │
│  │  │  │  Action: Turn OFF fogger immediately                       │   │   │   │
│  │  │  └────────────────────────────────────────────────────────────┘   │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌────────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │  Chamber: Maximum RH Safety                                │   │   │   │
│  │  │  │                                                             │   │   │   │
│  │  │  │  Trigger: RH > 95%                                          │   │   │   │
│  │  │  │  Action: Turn OFF fogger + notification                    │   │   │   │
│  │  │  └────────────────────────────────────────────────────────────┘   │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌────────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │  VPD System: Auto-start ved HASS oppstart                  │   │   │   │
│  │  │  │                                                             │   │   │   │
│  │  │  │  Trigger: Home Assistant start event                       │   │   │   │
│  │  │  │  Action:                                                    │   │   │   │
│  │  │  │  ├─ Wait 45s (entity loading)                              │   │   │   │
│  │  │  │  ├─ Enable all VPD automations                             │   │   │   │
│  │  │  │  ├─ Retry after 3s                                         │   │   │   │
│  │  │  │  ├─ Turn ON system (ventilation_pulse_mode)                │   │   │   │
│  │  │  │  └─ Send notification                                      │   │   │   │
│  │  │  └────────────────────────────────────────────────────────────┘   │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌────────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │  VPD System: Enable Critical Automations                   │   │   │   │
│  │  │  │                                                             │   │   │   │
│  │  │  │  Trigger: ventilation_pulse_mode → ON                      │   │   │   │
│  │  │  │  Action: Enable fogger & emergency stop automations        │   │   │   │
│  │  │  └────────────────────────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                           │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │   │
│  │  │  MOBILE NOTIFICATIONS                                             │   │   │
│  │  │                                                                    │   │   │
│  │  │  ┌────────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │  VPD Critical Alert (VPD > 0.35 kPa for 15 min)            │   │   │   │
│  │  │  │  Climate Health Critical (Score < 30% for 30 min)          │   │   │   │
│  │  │  │  Fogger Not Responding (VPD > 0.30 kPa for 60 min)         │   │   │   │
│  │  │  └────────────────────────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                          SCRIPT LAYER (Helpers)                          │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │   │
│  │  │  script.vpd_enable_all_automations                                │   │   │
│  │  │  └─ Manually enable fogger, emergency, ventilation automations    │   │   │
│  │  │                                                                    │   │   │
│  │  │  script.vpd_force_restart                                         │   │   │
│  │  │  ├─ Turn OFF system                                              │   │   │
│  │  │  ├─ Enable all automations                                       │   │   │
│  │  │  └─ Turn ON system                                               │   │   │
│  │  └───────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                      USER INTERFACE LAYER                                │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │   │
│  │  │  Lovelace Dashboard (Split-Screen Pro)                            │   │   │
│  │  │  ┌─────────────────────┬─────────────────────────────────────┐   │   │   │
│  │  │  │ LEFT COLUMN         │ RIGHT COLUMN                        │   │   │   │
│  │  │  ├─────────────────────┼─────────────────────────────────────┤   │   │   │
│  │  │  │ • System ON/OFF     │ • Phase Comparison Table            │   │   │   │
│  │  │  │ • Pinning/Fruiting  │ • Smart Alerts Panel                │   │   │   │
│  │  │  │ • VPD Settings      │ • Automation Status                 │   │   │   │
│  │  │  │ • Quick Actions:    │                                     │   │   │   │
│  │  │  │   - Enable Auto     │                                     │   │   │   │
│  │  │  │   - Force Restart   │                                     │   │   │   │
│  │  │  │   - Test Fogger     │                                     │   │   │   │
│  │  │  │   - Test Vifte      │                                     │   │   │   │
│  │  │  └─────────────────────┴─────────────────────────────────────┘   │   │   │
│  │  │  ┌───────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │ Grafana Dashboard (iframe, 12h history)                   │   │   │   │
│  │  │  │ • Temp/Humidity graph                                     │   │   │   │
│  │  │  │ • VPD graph with target annotations                       │   │   │   │
│  │  │  │ • Climate Health Score                                    │   │   │   │
│  │  │  │ • VPD Stability Score                                     │   │   │   │
│  │  │  │ • Equipment status cards                                  │   │   │   │
│  │  │  └───────────────────────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Notification API
                                   ▼
                     ┌──────────────────────────────┐
                     │    MOBILE DEVICE             │
                     │  ┌────────────────────────┐  │
                     │  │ Home Assistant App     │  │
                     │  │ • Push notifications   │  │
                     │  │ • Dashboard access     │  │
                     │  └────────────────────────┘  │
                     └──────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────┘

1. SENSOR ACQUISITION (every ~10 seconds)
   ┌───────────────┐
   │ Hardware      │
   │ Sensors       │ → WiFi/Zigbee → Home Assistant
   └───────────────┘
         │
         ▼
2. DATA AGGREGATION (template sensors, real-time)
   ┌───────────────────────────────────────────┐
   │ Average 3x temp → Chamber Avg Temp        │
   │ Average 3x RH → Chamber Avg Humidity      │
   └───────────────────────────────────────────┘
         │
         ▼
3. VPD CALCULATION (template sensor, real-time)
   ┌─────────────────────────────────────────────────────┐
   │ SVP = 0.61078 × e^((17.27×T)/(T+237.3))             │
   │ VPD = SVP × (1 - RH/100)                            │
   └─────────────────────────────────────────────────────┘
         │
         ▼
4. DYNAMIC SETPOINT (template sensor, real-time)
   ┌─────────────────────────────────────────────────────┐
   │ phase = pinning ? 0.15 kPa : 0.20 kPa               │
   │ target_RH = (1 - target_VPD/SVP) × 100              │
   └─────────────────────────────────────────────────────┘
         │
         ▼
5. AUTOMATION DECISION (every 2 min for fogger, 5 min for fan)
   ┌─────────────────────────────────────────────────────┐
   │ IF VPD > (target + hysteresis)                      │
   │ THEN fogger ON for 10s                              │
   │                                                      │
   │ IF time % 5 min == 0                                │
   │ THEN fan ON for 40s/65s (phase-dependent)           │
   └─────────────────────────────────────────────────────┘
         │
         ▼
6. EQUIPMENT CONTROL (real-time)
   ┌───────────────────────────────────────────┐
   │ switch.luftfukter → ON/OFF                │
   │ switch.hvit_vifte_switch → ON/OFF         │
   └───────────────────────────────────────────┘
         │
         ▼
7. FEEDBACK LOOP (sensor acquisition continues...)
   ┌─────────────────────────────────────────────────────┐
   │ New sensor readings → VPD recalculation             │
   │ → Next automation trigger evaluation                │
   └─────────────────────────────────────────────────────┘
```

## Control Logic Flowchart

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FOGGER CONTROL LOGIC (v3)                           │
└─────────────────────────────────────────────────────────────────────────┘

        ┌──────────────────┐
        │  Clock Tick      │
        │  (every 2 min)   │
        └────────┬─────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ System ON?         │
        │ (pulse_mode)       │
        └────────┬───────────┘
                 │
         ┌───────┴───────┐
         │ YES           │ NO → Exit
         ▼               └──────────────────────┐
┌────────────────────┐                         │
│ Read VPD sensor    │                         │
│ Read phase toggle  │                         │
└────────┬───────────┘                         │
         │                                      │
         ▼                                      │
┌────────────────────────────┐                 │
│ target = 0.15 (pinning) ?  │                 │
│        : 0.20 (fruiting)   │                 │
└────────┬───────────────────┘                 │
         │                                      │
         ▼                                      │
┌────────────────────────────┐                 │
│ VPD > target + 0.03 ?      │                 │
└────────┬───────────────────┘                 │
         │                                      │
   ┌─────┴─────┐                                │
   │ YES       │ NO → Exit                      │
   ▼           └──────────────────────┐         │
┌──────────────────┐                  │         │
│ Turn ON fogger   │                  │         │
└────────┬─────────┘                  │         │
         │                             │         │
         ▼                             │         │
┌──────────────────┐                  │         │
│ Wait 10 seconds  │                  │         │
└────────┬─────────┘                  │         │
         │                             │         │
         ▼                             │         │
┌──────────────────┐                  │         │
│ Turn OFF fogger  │                  │         │
└────────┬─────────┘                  │         │
         │                             │         │
         └─────────────────────────────┴─────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │ Wait 2 minutes │
                              │ (next trigger) │
                              └────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    EMERGENCY STOP LOGIC (v3)                             │
└─────────────────────────────────────────────────────────────────────────┘

        ┌──────────────────┐
        │  VPD Sensor      │
        │  Update Event    │
        └────────┬─────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ System ON?         │
        │ (pulse_mode)       │
        └────────┬───────────┘
                 │
         ┌───────┴───────┐
         │ YES           │ NO → Exit
         ▼               └────────────────┐
┌────────────────────┐                   │
│ Read VPD           │                   │
│ Read target VPD    │                   │
└────────┬───────────┘                   │
         │                                │
         ▼                                │
┌───────────────────────────┐            │
│ VPD < target - 0.03 ?     │            │
│ (for 30 seconds)          │            │
└────────┬──────────────────┘            │
         │                                │
   ┌─────┴─────┐                          │
   │ YES       │ NO → Exit                │
   ▼           └──────────────────┐       │
┌──────────────────────┐          │       │
│ EMERGENCY STOP       │          │       │
│ Turn OFF fogger      │          │       │
└────────┬─────────────┘          │       │
         │                         │       │
         ▼                         │       │
┌──────────────────────┐          │       │
│ Log event            │          │       │
└────────┬─────────────┘          │       │
         │                         │       │
         └─────────────────────────┴───────┘
```

## Component Interaction Matrix

```
┌─────────────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│             │Sensor│Templ │Auto  │Script│Switch│Input │Notify│
│ Component   │      │Sensor│mation│      │      │Bool  │      │
├─────────────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│ Temp Sensor │  -   │  →   │      │      │      │      │      │
│ RH Sensor   │  -   │  →   │      │      │      │      │      │
│ Avg Temp    │  ←   │  -   │  →   │      │      │      │      │
│ Avg RH      │  ←   │  -   │  →   │      │      │      │      │
│ VPD Calc    │      │  ←   │  →   │      │      │      │      │
│ Dyn RH Set  │      │  ←   │  →   │      │      │  ←   │      │
│ Fogger Auto │      │  ←   │  -   │      │  →   │  ←   │      │
│ Vent Auto   │      │      │  -   │      │  →   │  ←   │      │
│ Emerg Auto  │      │  ←   │  -   │      │  →   │      │  →   │
│ Auto-start  │      │      │  →   │      │      │  →   │  →   │
│ Enable Auto │      │      │  →   │  -   │      │      │  →   │
│ Fogger SW   │      │      │  ←   │      │  -   │      │      │
│ Fan Switch  │      │      │  ←   │      │  -   │      │      │
│ Pulse Mode  │      │      │  ←   │  ←   │      │  -   │      │
│ Phase Toggle│      │  →   │  ←   │      │      │  -   │      │
│ Notification│      │      │  ←   │  ←   │      │      │  -   │
└─────────────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Legend:
  →  = Provides data to
  ←  = Receives data from
  -  = Self-reference
```

## State Machine Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VPD SYSTEM STATE MACHINE                          │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
         ┌─────────►│   BOOT/INIT      │
         │          │ (All automations │
         │          │  may be disabled)│
         │          └────────┬─────────┘
         │                   │
         │                   │ Auto-start trigger
         │                   │ (45s delay)
         │                   ▼
         │          ┌──────────────────┐
         │          │   ENABLING       │
         │          │ (Re-enable all   │
         │          │  automations)    │
         │          └────────┬─────────┘
         │                   │
         │                   │ Success
         │                   ▼
         │          ┌──────────────────┐
         │      ┌───┤   SYSTEM ON      │◄────┐
         │      │   │ (pulse_mode=ON)  │     │
         │      │   │                  │     │
         │      │   │ • Fogger Auto: ✅│     │
         │      │   │ • Vent Auto: ✅  │     │
         │      │   │ • Emerg Auto: ✅ │     │
         │      │   └────────┬─────────┘     │
         │      │            │                │
         │      │            │ User toggle    │
         │      │            │ OFF            │
         │      │            ▼                │
         │      │   ┌──────────────────┐     │
         │      │   │   SYSTEM OFF     │     │
         │      │   │ (pulse_mode=OFF) │     │
         │      │   │                  │     │
         │      │   │ • Fogger: Idle   │     │
         │      │   │ • Vent: Stopped  │     │
         │      │   │ • Emerg: Monitor │     │
         │      │   └────────┬─────────┘     │
         │      │            │                │
         │      │            │ User toggle ON │
         │      │            │ (triggers      │
         │      │            │  enable auto)  │
         │      │            └────────────────┘
         │      │
         │      │  WITHIN SYSTEM ON STATE:
         │      │  ┌────────────────────────────────────┐
         │      │  │                                    │
         │      └─►│  ┌──────────────┐                 │
         │         │  │   PINNING    │                 │
         │         │  │ Target: 0.15 │                 │
         │         │  │ ACH: 4       │                 │
         │         │  └──────┬───────┘                 │
         │         │         │                          │
         │         │         │ Phase toggle             │
         │         │         ▼                          │
         │         │  ┌──────────────┐                 │
         │         │  │  FRUITING    │                 │
         │         │  │ Target: 0.20 │                 │
         │         │  │ ACH: 7       │                 │
         │         │  └──────────────┘                 │
         │         │                                    │
         │         └────────────────────────────────────┘
         │
         │  SYSTEM ON → Restart Home Assistant
         └──────────────────────────────────────────────┘
```

---

**End of System Architecture Document**

```

---

# CHANGELOG.md
> Endringshistorikk

```markdown
# VPD Control System v3 - Changelog

All notable changes to this project are documented in this file.

---

## [3.7.0] - 2026-04-24

### Added
- **Ventilation: Timer Idle Watchdog (Lag 3)** (`automation.ventilation_timer_idle_watchdog`)
  - Tredje lag i "evighetsmaskin"-design: restarter `timer.ventilation_cycle` hvis den har
    vært idle i >30 minutter mens `ventilation_pulse_mode` er ON
  - Terskel 30 min = 14× normal max idle-tid (~120s) — null falske positiver
  - Restarter timer med 30s slik at `ventilation_timer_v4` tar over naturlig
  - Sender push-varsling med tidsstempel for post-mortem analyse
  - Rotårsak til bug: `ventilation_timer_v4` feiler stille ~daglig kl 04–06 CEST
    (mistenkt HA intern jobb ~03:00 UTC — recorder cleanup)

### Fixed
- **Fan Watchdog restarter nå ventilasjonssyklus** (`fan_watchdog_safety`)
  - Tidligere: watchdog slo av viften men startet ikke `timer.ventilation_cycle` på nytt
  - Ventilasjonssyklusen stoppet permanent etter watchdog-utløsning
  - Fix: lagt til `timer.start` etter fan turn-off (betinget på pulse_mode=on)
- **Fuktighets-kalibrering: Aqara T1 primary sensorer** (2-timers side-by-side, Inkbird referanse)
  - `chamber_sensor_1`: leser -3.1% vs Inkbird → +3.0% offset i `chamber_avg_humidity` template
  - `chamber_sensor_2`: leser -2.9% vs Inkbird → +3.0% offset i `chamber_avg_humidity` template
  - `kammeret` (fallback): leser +0.5% vs Inkbird → ingen offset
  - `chamber_avg_humidity` rapporterer nå korrekt ~96% faktisk fuktighet
- **float(9.99) bug i fogger_inactivity_alert**
  - Falske varsler når `sensor.chamber_current_vpd` var unavailable
  - Erstattet `float(9.99)` fallback med `{% if vpd_raw in ['unknown','unavailable'] %}` pattern
- **anomaly_sensor_offline meldingstekst**: erstattet `sensor.kammeret_humidity` referanse
  med `sensor.chamber_sensor_1_humidity`
- **Fogger-description**: oppdatert fra "12s" til "14s (23% duty cycle)"

### Infrastructure
- **Sensor-migrasjon Aqara T1**: 2x Sonoff SNZB-02WD byttet ut med 2x Aqara T1 (ZHA re-paring
  2026-04-21 etter ZHA-koordinator restart). ZHA offset ikke tilgjengelig på Aqara T1 —
  kalibrering gjøres i template-sensor.

### Tre-lags ventilasjonssikkerhet etter denne versjonen

| Lag | Automation | Trigger | Handling |
|---|---|---|---|
| 1 | `fan_watchdog_safety` | Fan ON >150s | Slår av fan, starter timer |
| 2 | `ventilation_pulse_start` | pulse_mode → on | Starter timer |
| 3 | `ventilation_timer_idle_watchdog` | Timer idle >30 min | Starter timer (30s), varsler bruker |

---

## [3.6.0] - 2026-02-23

### Added
- **Ny automation: "VPD Control: Fog After Ventilation"** (`automation.vpd_control_fog_after_ventilation`)
  - Proaktiv 14s fogger-burst rett etter at viften slår AV (trigger: `vifter_switch → off`)
  - Trigger-terskel: `vpd >= target_vpd` (0.12 kPa fruiting) — lavere enn reaktiv fogger
  - Conditions: `ventilation_pulse_mode on`, `fogger_switch off` (forhindrer dobbel-trigger)
  - **Formål:** Kompenserer for humidity-drop fra ventilasjon UMIDDELBART istedenfor å vente
    på sensor-rapportering (~10-15 min lag). Gir ~12 jevnt fordelte bursts per time.
  - Lagt til i enable/disable/auto-start automation-lister for komplett systemstyring

### Changed
- **VPD Hysteresis økt fra 0.01 → 0.02 kPa** (`input_number.vpd_hysteresis`)
  - Ny reaktiv trigger-terskel: VPD ≥ 0.12 + 0.02 = **0.14 kPa** (fra 0.13)
  - Eliminerer "kun S1 falt"-sesjoner der avg=92.4%, VPD=0.13 (sensor-asym ved T<16°C)
  - Proaktiv automation (se over) håndterer nå baseline-kompensasjonen ved threshold 0.12
  - Emergency stop threshold: 0.12 - 0.02 = 0.10 kPa

### Background (data-analyse 04:00–16:00, 2026-02-23)
- System oscillerte mellom RH 90.9% (trough) og 93.9% (peak) = 3.1% sving
- Tid ved/over setpoint (~93.8% @ 17°C): kun ~40-50% av perioden
- Fogger cluster: 4-11 påfølgende minutt-bursts, deretter 10-15 min hvile
- Rotårsak: reaktivt system responderer på sensor-rapportering (~10-15 min lag)
  etter at humidity allerede har droppet under setpoint pga. ventilasjon hvert 5. min
- Forventet forbedring: trough hever seg til >92%, RH over setpoint >60-70% av perioden

### Verified (data-analyse 22:00–08:00, 2026-02-23/24)
Første natt med ny automation + hysteresis 0.02 — bekreftet forbedring:

| Metrikk | FØR (04:00–16:00) | ETTER (22:00–08:00) |
|---------|-------------------|---------------------|
| Fog-mønster | Cluster 7–11 bursts, pause 10–15 min | **1 burst/5 min** (synkronisert med fan) |
| avg RH trough | 90.8–90.9% | 91.2% (+0.3%) |
| avg RH peak | 93.8–93.9% | 94.2–94.5% (+0.4–0.6%) |
| RH-sving | 3.1% | ~2.3–2.5% (−0.6–0.8%) |
| Reaktive sesjoner/time | ~3.4 | ~2.2 (−35%) |
| Sesjonslengde | 4–11 bursts | 3–6 bursts |

Observasjoner:
- **Proaktiv fog virker:** 1 burst umiddelbart etter fan OFF, perfekt synkronisert
- **Smart skip virker:** Ingen proaktiv burst når VPD < 0.12 kPa (forhindrer overskudd)
- **Trough forbedret minimalt (+0.3%):** Sensorer rapporterer kun ~hvert 15. min —
  drops skjer fremdeles mellom rapporteringer, utenfor systemets kontroll
- **Peak RH høyere:** Systemet holder nå RH over setpoint større andel av tiden
- Gjenstående utfordring er sensorlag + fysikk, ikke logikk — ingen ytterligere
  kodeendringer anbefalt foreløpig

---

## [3.6.1] - 2026-02-24

### Infrastructure
- **GitHub PAT satt opp for Claude-basert git push**
  - GitHub Credential Manager (GCM) blokkerte push fra Claude sitt miljø (browser-avhengig auth)
  - Løsning: PAT med `repo`-scope lagret via `git credential approve` i Windows Credential Manager
  - `git push origin main` fungerer nå direkte uten manuell intervensjon
  - Se `claude-setup.md` → Git Workflow → GitHub Push Authentication for fornyelsesprosedyre

---

## [3.5.3] - 2026-02-19

### Changed
- **Fogger burst økt fra 12s til 14s** (+16.7% humidifisering per burst)
  - System observert med burst-klynger (mange bursts på rad) — tyder på underkapasitet
  - 14s burst gir mer fuktighet per syklus og reduserer antall burst-klynger

---

## [3.5.2] - 2026-02-19

### Changed
- **Inaktivitetsalert terskel økt fra 15 til 30 minutter** for både fogger og vifte
  - 15 min var for aggressivt — foggeren kan legitimt ligge stille lenge når RH er høy
  - Alias oppdatert: `VPD Alert: Fogger/Vifte Inaktiv 30 min`

---

## [3.5.1] - 2026-02-18

### Fixed
- **Chamber Avg Humidity bruker nå kalibrerte SNZB-02WD-sensorer** i stedet for Netatmo (`sensor.kammeret_humidity`)
  - Netatmo-kilden var en midlertidig løsning fra v3.4.0 — nå fjernet
  - Template bruker `sensor.chamber_sensor_1_humidity` + `sensor.chamber_sensor_2_humidity` med graceful degradation
  - Kalibrering gjøres via ZHA offset-entiteter i HA UI: `number.chamber_sensor_1_humidity_offset` (+8.5%) og `number.chamber_sensor_2_humidity_offset` (+8.2%)
  - Oppdaget at SNZB-02WD underrapporterer ~8-9% ved høy fuktighet; SNZB-02P underrapporterer ~2-3%

---

## [3.5.0] - 2026-02-18

### Fixed
- **CRITICAL: Fan automation not re-enabled after system ON/OFF cycle**
  - `VPD System: Enable Critical Automations` re-enabled only fogger automations, not `ventilation_time_pattern_udodelig`
  - Viften stoppet å virke etter manuell system-toggle (ON→OFF→ON) og kjørte ikke igjen uten HA-restart
  - Fikset ved å legge til `automation.ventilation_time_pattern_udodelig` i re-enable-listen

### Added
- **Fan Watchdog: Safety Shutoff** — slår automatisk av viften etter 120s (fruiting max 75s + 45s margin). Sender mobilvarsel. Identisk mønster som fogger watchdog (30s).
- **VPD Alert: Fogger Inaktiv 15 min** — varsler hvis foggeren ikke har slått seg på på 15 minutter mens systemet er aktivt. Inkluderer nåværende VPD i meldingen.
- **VPD Alert: Vifte Inaktiv 15 min** — varsler hvis ventilasjonsviften ikke har slått seg på på 15 minutter mens systemet er aktivt.

### Changed
- Auto-start notifikasjon rettet: viste fortsatt `10s bursts (16.7%)`, nå korrekt `12s bursts (20%)`

---

## [3.4.0] - 2026-02-14

### Changed
- **Sensor Migration:** Erstattet Netatmo + ESPHome-sensorer med 4x Sonoff Zigbee-sensorer
  - 2x SNZB-02WD i fruiting chamber (`sensor.chamber_sensor_1_*`, `sensor.chamber_sensor_2_*`)
  - 2x SNZB-02P i incubation room (`sensor.incubation_sensor_1_*`, `sensor.incubation_sensor_2_*`)
  - VPD kalkuleres nå fra template-sensor (`sensor.chamber_current_vpd`) i stedet for ESPHome
- **Two-tier sensor architecture:** Raw ZHA → avg template → VPD calc. Graceful degradation ved én utilgjengelig sensor.
- **Incubation room monitoring** lagt til (ingen VPD-kontroll, kun logging)
- Alle filer oppdatert: configuration, automations, dashboard, README

---

## [3.3.0] - 2026-02-09

### Changed
- **VPD Targets:** Pinning 0.15 → 0.10 kPa, Fruiting 0.20 → 0.12 kPa
- **Temperature Targets:** Fruiting 18°C → 17°C (Pinning stays 15°C)
- **Ventilation Durations:** Pinning 40s → 60s (6 ACH), Fruiting 65s → 75s (8 ACH)
- **RH Targets:** ~91% → ~94% for both phases (dynamic, calculated from VPD)
- **Dashboard card_mod:** Animations now target icon only (`mushroom-shape-icon$`) instead of entire card (`ha-card`). Fogger icon pulses, fan icon spins.

### Removed
- **Netatmo sensor failsafe:** Moved out of VPD automation file (not VPD-related)
- **Evelina i fallet:** Moved out of VPD automation file (not VPD-related)

---

## [3.2.0] - 2026-02-09

### Fixed
- **CRITICAL: Switch Entity IDs:** All automations and sensors now use correct entity IDs
  - `switch.luftfukter` (didn't exist) → `switch.fogger_switch` (ZHA)
  - `switch.hvit_vifte_switch` (didn't exist) → `switch.vifter_switch` (ZHA)
  - `switch.vifte_canfan_switch` (old) → `switch.vifter_switch` (ZHA)
  - This fix means fogger and fan actually respond to automations now
- **Automation Entity ID References:** HA generates entity_id from `alias` field, not `id` field
  - `automation.vpd_control_fogger_burst_v3` → `automation.vpd_control_fogger_burst`
  - `automation.vpd_control__emergency_stop_v3` → `automation.vpd_control_emergency_stop_fogger`
  - `automation.ventilation_time_pattern_v3` → `automation.ventilation_time_pattern_udodelig`
- **Dashboard card_mod:** Fixed entity references (`switch.fogger` → `switch.fogger_switch`)
- **HA Entity Registry:** Cleaned ghost/duplicate entity registrations
- **Fogger Trigger:** `seconds: /60` is invalid in HA time_pattern (must be 0-59), changed to `minutes: /1`
- **Auto-start notification:** Updated duty cycle text to 16.7% (was 8.3%)

### Added
- **Safety Automations** (imported from legacy automations.yaml):
  - Fogger Watchdog: auto-off after 30 seconds (hardware failsafe)
  - Ventilation Safety Net: fan forced OFF on HA startup
  - VPD System Disable: deactivates all automations + hardware when system OFF
  - Chamber Light Auto ON (06:00) / OFF (18:00)
- **48h Pinning Phase Auto-Return:**
  - Timer starts when pinning activated
  - Auto-switches to fruiting after 48 hours
  - Cancels on manual phase change
  - Mobile notifications for start/finish
- **Sensor Anomaly Detection:**
  - Rapid temperature change (>1°C/5min)
  - Rapid humidity change (>5%/5min)
  - Sensor offline detection (Critical/Degraded)
  - Temperature out of range (14-20°C)
  - Humidity out of range (60-97%)
- **Daily Morning Status Report** (08:00):
  - System status, phase, VPD/temp/RH readings
  - Health scores, sensor status
  - Dashboard link
- **Dashboard Enhancements:**
  - Climate Health card with color-coded background (green/yellow/red)
  - VPD Stability card with color-coded background
  - Pinning phase countdown display
- **Template Sensors:**
  - `sensor.sensor_health_status` (Healthy/Degraded/Critical)
  - `sensor.temp_change_5min` (rate-of-change, trigger-based)
  - `sensor.humidity_change_5min` (rate-of-change, trigger-based)

---

## [3.1.0] - 2025-12-17

### Changed
- **Fogger Burst Duration:** Increased from 7s to 10s
  - Duty cycle: 5.8% → 8.3% (+43% increase)
  - Rationale: Better humidity control, addresses RH consistently 2-5% below target
  - Effective fogging time: ~8-9s (compensates for 1-2s startup lag)
  - Expected result: RH stays closer to target, fewer large drops after ventilation

### Why This Update?
User observed humidity consistently falling below target RH, with large drops (82-90% range instead of 88-95%). Analysis showed fogger duty cycle (5.8%) was insufficient to compensate for chamber drying rate and ventilation moisture removal.

---

## [3.0.0] - 2025-12-17

### Added
- **Complete System Refactor:** VPD Control System v3
- **Immortal Time-Pattern Triggers:** Clock-based automation (cannot fail)
  - Fogger: Every 2 minutes (`time_pattern: minutes: /2`)
  - Ventilation: Every 5 minutes (`time_pattern: minutes: /5`)
  - No dependency on timers or helper entities
- **Auto-Start System:**
  - Activates all critical automations on Home Assistant boot
  - 45s delay for entity loading
  - Retry logic with `homeassistant.turn_on` service
  - Persistent notification with automation status
- **Manual Enable Automation:**
  - Triggers when `ventilation_pulse_mode` turns ON
  - Automatically enables fogger and emergency stop automations
- **Helper Scripts:**
  - `script.vpd_enable_all_automations` - Manual enable button
  - `script.vpd_force_restart` - Full system restart with automation enable
- **Dashboard Integration:**
  - Split-screen Mushroom dashboard
  - Grafana iframe for 12h historical graphs
  - Quick Actions panel with Enable Auto and Force Restart buttons
  - Automation Status Panel (real-time markdown template)
  - Phase Comparison Table
  - Smart Alerts Panel
- **Mobile Notifications:**
  - VPD Critical (>0.35 kPa for 15 min)
  - Climate Health Critical (<30% for 30 min)
  - Fogger Not Responding (VPD >0.30 kPa for 60 min)
- **Comprehensive Documentation:**
  - Complete README (installation, usage, troubleshooting)
  - System Architecture diagram
  - Grafana setup instructions
  - Quick reference card

### Changed
- **Fogger Control:** Decoupled from ventilation
  - No timer dependencies
  - Independent 2-minute time_pattern trigger
  - Simplified logic: Check VPD → Run burst → Exit
- **Ventilation Control:** Decoupled from fogger
  - Independent 5-minute time_pattern trigger
  - Phase-dependent duration (40s pinning, 65s fruiting)
  - "Udødelig" (immortal) - cannot fail
- **Emergency Stop:** Enhanced logic
  - 30s delay before triggering
  - Template-based VPD threshold check
  - Immediate fogger shutoff
- **Climate Health Score:** Updated to use VPD v3 entities
  - Changed from `input_boolean.kammer_pinning_active` → `input_boolean.pinning_phase`
  - Changed from `sensor.chamber_target_rh` → `sensor.dynamic_rh_setpoint`
  - Hardcoded temperature targets (15°C pinning, 18°C fruiting)
- **Extraction Fan:** Updated entity reference
  - Changed from `switch.vifte_canfan_switch` → `switch.vifter_switch` (ZHA)
  - Old fan deactivated, new fan has same function

### Fixed
- **Automation Persistence Bug:**
  - Automations disabled in UI remained disabled after restart
  - Solution: Auto-start uses `homeassistant.turn_on` to re-enable
  - Manual "Enable Auto" button for immediate recovery
- **Timer Failure Vulnerability:**
  - Removed timer dependencies (timer.ventilation_cycle)
  - Timer could fail, causing entire system to stop
  - Time-pattern triggers cannot fail (immortal)
- **Entity ID Mismatch:**
  - Fixed automation entity_id references in scripts and dashboard
  - Correct mapping: automation ID → entity_id format
  - Note: HA generates entity_id from alias, not id field (fixed properly in v3.2.0)
- **Fogger Startup Lag:**
  - Increased burst from 5s → 7s → 10s
  - Compensates for 1-2s ultrasonic fogger ramp-up time
  - Effective fogging now ~8-9s per cycle

### Removed
- **Timer-Based Automation:** Removed `timer.ventilation_cycle` dependency
- **Pre-fogging:** Removed complex pre-ventilation fogging logic
- **Coupled Fogger-Ventilation:** Removed interdependencies

---

## [2.0.0] - 2024-XX-XX

### Added
- **Dynamic RH Setpoint:** Calculate target RH based on temperature and target VPD
  - Formula: `target_RH = (1 - target_VPD/SVP) × 100`
  - Adjusts automatically for temperature fluctuations
- **Dual-Phase Control:**
  - Pinning Phase (15°C, 0.15 kPa VPD)
  - Fruiting Phase (18°C, 0.20 kPa VPD)
  - One-click phase toggle
- **VPD-Based Hysteresis Control:**
  - Configurable hysteresis (default 0.03 kPa)
  - Prevents rapid fogger cycling
  - Dead zone: ±0.03 kPa from target
- **Climate Health Score:**
  - Composite metric (0-100%)
  - Weighted: 40% VPD stability + 40% RH efficiency + 20% temp accuracy
- **VPD Stability Score:**
  - Measures VPD deviation from target over time
  - 0-100% scale (100% = perfect stability)
- **Template Sensors:**
  - `sensor.chamber_current_vpd` - Real-time VPD calculation
  - `sensor.vpd_stability_score` - VPD stability metric
  - `sensor.humidity_control_efficiency` - RH control metric
  - `sensor.climate_health_score` - Overall system health

### Changed
- **Control Logic:** Switched from RH threshold to VPD threshold
- **Sensor Averaging:** Average 3 temp and 3 humidity sensors for accuracy

---

## [1.0.0] - 2024-XX-XX

### Added
- **Initial Release:** Basic humidity control system
- **RH Threshold Control:** Simple high/low threshold with hysteresis
- **Timer-Based Automation:** Uses `timer.ventilation_cycle`
- **Single-Phase Operation:** Fixed temperature and RH targets
- **Equipment Control:**
  - Fogger (switch.luftfukter)
  - Extraction fan (switch.vifte_canfan_switch)
- **Basic Safety:**
  - Maximum RH cutoff at 95%
  - Emergency stop on sensor unavailable

---

## Migration Guide

### From v2.0 to v3.0

1. **Backup existing configuration:**
   ```bash
   cp automations.yaml automations_backup_v2.yaml
   cp configuration.yaml configuration_backup_v2.yaml
   ```

2. **Update automations:**
   - Replace timer-based automations with time_pattern versions
   - Add auto-start automation
   - Add enable automation
   - Update entity references (chamber → vpd, kammer → pinning_phase)

3. **Update scripts.yaml:**
   - Add `vpd_enable_all_automations`
   - Add `vpd_force_restart`

4. **Update dashboard:**
   - Replace old dashboard with `vpd_dashboard_split_screen_pro.yaml`
   - Install Mushroom cards via HACS
   - Optional: Set up Grafana integration

5. **Test system:**
   ```yaml
   # Developer Tools → Services
   service: script.vpd_enable_all_automations
   ```

6. **Verify automation status:**
   - Check dashboard Automation Status Panel
   - All should show "✅ Enabled"

### From v1.0 to v3.0

**Major breaking changes - full reinstall recommended.**

1. Complete backup of configuration
2. Follow installation instructions in README.md
3. Migrate entity_ids from old sensors to new template sensors
4. Recalibrate parameters (targets changed from RH to VPD)

---

## Known Issues

### v3.5.1
- None currently known

### v3.5.0
- None currently known

### v3.4.0
- None currently known

### v3.3.0
- None currently known

### v3.2.0
- None currently known

### v3.0.0 (Fixed in v3.2.0)
- ~~**Dashboard entity_id mapping:** Automation entity_ids must match automation `id:` field (not `alias:`)~~ — Fixed in v3.2.0: HA generates entity_id from alias, all references corrected
- ~~**Wrong switch entity IDs:** `switch.luftfukter` and `switch.hvit_vifte_switch` didn't exist~~ — Fixed in v3.2.0
- **Grafana iframe CORS:** May require `allow_embedding = true` in grafana.ini
  - Solution: See GRAFANA_SETUP_INSTRUCTIONS.md

---

## Upcoming Features (Roadmap)

- [ ] **Temperature Control:** Add thermostat integration for active heating/cooling
- [ ] **CO2 Monitoring:** Integrate CO2 sensor feedback into ventilation logic
- [ ] **Machine Learning:** Predict optimal fogger timing based on historical data
- [ ] **Multi-Chamber Support:** Control multiple chambers from single instance
- [ ] **Advanced Notifications:** SMS, email, webhook integrations
- [ ] **Preset Profiles:** Species-specific VPD/temp profiles (oyster, shiitake, lion's mane, etc.)
- [ ] **Energy Monitoring:** Track fogger/fan power consumption
- [ ] **Maintenance Scheduler:** Automated reminders for cleaning, calibration

---

## Support & Contributions

For bugs, feature requests, or questions:
- Check README.md troubleshooting section
- Review automation traces in Home Assistant
- Check system logs for errors

---

**Version Naming Scheme:**
- **Major (X.0.0):** Breaking changes, architecture refactors
- **Minor (x.X.0):** New features, non-breaking changes
- **Patch (x.x.X):** Bug fixes, documentation updates

```

---

# configuration_vpd_sensors.yaml
> HA konfigurasjon: template-sensorer

```yaml
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

# VPD Control System
input_number: !include input_numbers_vpd.yaml
input_boolean: !include input_booleans_vpd.yaml
timer: !include timer_vpd.yaml

# Mushroom cards (loaded via HACS)
# Remove tibber_custom - not a valid integration

homeassistant:
  allowlist_external_dirs:
    - /config/www

# Sopp Tracker Frontend - Shell commands for autostart
# Frontend files in /config/www/sopp-tracker/
# Backend runs in Docker on port 8000
shell_command:
  start_sopp_frontend: 'nohup python3 -m http.server 3001 --bind 0.0.0.0 --directory /config/www/sopp-tracker > /dev/null 2>&1 &'
  stop_sopp_frontend: 'pkill -f "python3 -m http.server 3001"'
  restart_sopp_frontend: 'pkill -f "python3 -m http.server 3001"; sleep 2; nohup python3 -m http.server 3001 --bind 0.0.0.0 --directory /config/www/sopp-tracker > /dev/null 2>&1 &'

camera:
  - platform: generic
    name: Værbilde
    still_image_url: https://www.var.hht.no/forsidebilde.jpg
    limit_refetch_to_url_change: false

# ═══════════════════════════════════════════════════════════════════════════════
# MUSHROOM CHAMBER - CONFIGURATION.YAML v3.0 FINAL + STATISTICS
# Basert på faktiske entities i ditt HA
# ═══════════════════════════════════════════════════════════════════════════════

template:
  - sensor:
      # ─────────────────────────────────────────────────────────────────────────
      # BASE SENSORS (EKSISTERER ALLEREDE)
      # ─────────────────────────────────────────────────────────────────────────
      
      # Average Temperature (2x Aqara T1, fallback: sensor.kammeret_temperature)
      - name: "Chamber Avg Temp"
        unique_id: chamber_avg_temp
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        state: >
          {% set t1 = states('sensor.chamber_sensor_1_temperature') | float(none) %}
          {% set t2 = states('sensor.chamber_sensor_2_temperature') | float(none) %}
          {% set valid = [] %}
          {% if t1 is not none and t1 > 5 and t1 < 35 %}
            {% set valid = valid + [t1] %}
          {% endif %}
          {% if t2 is not none and t2 > 5 and t2 < 35 %}
            {% set valid = valid + [t2] %}
          {% endif %}
          {% if valid | length > 0 %}
            {{ (valid | sum / valid | length) | round(1) }}
          {% else %}
            {% set tk = states('sensor.kammeret_temperature') | float(none) %}
            {% if tk is not none and tk > 5 and tk < 35 %}
              {{ tk | round(1) }}
            {% else %}
              18.0
            {% endif %}
          {% endif %}
        availability: >
          {{ states('sensor.chamber_sensor_1_temperature') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.chamber_sensor_2_temperature') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.kammeret_temperature') not in ['unavailable', 'unknown', 'none'] }}

      # Average Humidity (2x Aqara T1, fallback: sensor.kammeret_humidity)
      - name: "Chamber Avg Humidity"
        unique_id: chamber_avg_humidity
        unit_of_measurement: "%"
        device_class: humidity
        state_class: measurement
        state: >
          {% set h1_raw = states('sensor.chamber_sensor_1_humidity') | float(none) %}
          {% set h2_raw = states('sensor.chamber_sensor_2_humidity') | float(none) %}
          {% set h1 = (h1_raw + 3.0) if h1_raw is not none else none %}
          {% set h2 = (h2_raw + 3.0) if h2_raw is not none else none %}
          {% set valid = [] %}
          {% if h1 is not none and h1 > 30 and h1 < 100 %}
            {% set valid = valid + [h1] %}
          {% endif %}
          {% if h2 is not none and h2 > 30 and h2 < 100 %}
            {% set valid = valid + [h2] %}
          {% endif %}
          {% if valid | length > 0 %}
            {{ (valid | sum / valid | length) | round(1) }}
          {% else %}
            {% set hk = states('sensor.kammeret_humidity') | float(none) %}
            {% if hk is not none and hk > 30 and hk < 100 %}
              {{ hk | round(1) }}
            {% else %}
              85.0
            {% endif %}
          {% endif %}
        availability: >
          {{ states('sensor.chamber_sensor_1_humidity') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.chamber_sensor_2_humidity') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.kammeret_humidity') not in ['unavailable', 'unknown', 'none'] }}

      # Target RH (OLD - deprecated, use sensor.dynamic_rh_setpoint instead)
      # Kept for backward compatibility only
      - name: "Chamber Target RH"
        unique_id: chamber_target_rh
        unit_of_measurement: "%"
        device_class: humidity
        state: >
          {{ states('sensor.dynamic_rh_setpoint') | float(93) }}
        availability: >
          {{ states('sensor.dynamic_rh_setpoint') not in ['unavailable', 'unknown', 'none'] }}

      # Current VPD (monitoring)
      - name: "Chamber Current VPD"
        unique_id: chamber_current_vpd
        unit_of_measurement: "kPa"
        state_class: measurement
        state: >
          {% set T = states('sensor.chamber_avg_temp') | float(18) %}
          {% set RH = states('sensor.chamber_avg_humidity') | float(85) %}
          {% set SVP = 0.61078 * (2.71828 ** ((17.27 * T) / (T + 237.3))) %}
          {% set VPD = SVP * (1 - (RH / 100)) %}
          {{ VPD | round(2) }}
        availability: >
          {{ states('sensor.chamber_avg_temp') not in ['unavailable', 'unknown', 'none'] and
             states('sensor.chamber_avg_humidity') not in ['unavailable', 'unknown', 'none'] }}

      # ─────────────────────────────────────────────────────────────────────────
      # STATISTICS SENSORS (NYE)
      # ─────────────────────────────────────────────────────────────────────────
      
      # VPD STABILITY INDEX (24h) - VPD v3 Compatible
      - name: "VPD Stability Score"
        unique_id: vpd_stability_score
        unit_of_measurement: "%"
        state_class: measurement
        state: >
          {% set pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 0.10 if pinning else 0.12 %}
          {% set vpd = states('sensor.chamber_current_vpd') | float(0) %}
          {% set deviation = (vpd - target) | abs %}
          {% if deviation < 0.03 %}
            100
          {% elif deviation < 0.08 %}
            {{ (100 - (deviation - 0.03) * 1000) | round(0) }}
          {% elif deviation < 0.15 %}
            {{ (50 - (deviation - 0.08) * 714) | round(0) }}
          {% else %}
            0
          {% endif %}
        icon: mdi:chart-line-variant
        availability: >
          {{ states('sensor.chamber_current_vpd') not in ['unavailable', 'unknown', 'none'] }}

      # HUMIDITY CONTROL EFFICIENCY - VPD v3 Compatible
      - name: "Humidity Control Efficiency"
        unique_id: humidity_control_efficiency
        unit_of_measurement: "%"
        state_class: measurement
        state: >
          {% set current_rh = states('sensor.chamber_avg_humidity') | float(0) %}
          {% set target_rh = states('sensor.dynamic_rh_setpoint') | float(93) %}
          {% set deviation = (current_rh - target_rh) | abs %}
          {% if deviation < 2 %}
            100
          {% elif deviation < 5 %}
            {{ (100 - (deviation - 2) * 20) | round(0) }}
          {% elif deviation < 10 %}
            {{ (40 - (deviation - 5) * 8) | round(0) }}
          {% else %}
            0
          {% endif %}
        icon: mdi:water-check
        availability: >
          {{ states('sensor.chamber_avg_humidity') not in ['unavailable', 'unknown', 'none'] and
             states('sensor.dynamic_rh_setpoint') not in ['unavailable', 'unknown', 'none'] }}

      # HUMIDIFIER RUNTIME PERCENTAGE (24h estimate) - VPD v3 Compatible
      - name: "Humidifier Runtime Percent"
        unique_id: humidifier_runtime_percent
        unit_of_measurement: "%"
        state_class: measurement
        state: >
          {% set current_rh = states('sensor.chamber_avg_humidity') | float(0) %}
          {% set target_rh = states('sensor.dynamic_rh_setpoint') | float(93) %}
          {% if current_rh < target_rh - 3 %}
            100
          {% elif current_rh < target_rh + 3 %}
            50
          {% else %}
            0
          {% endif %}
        icon: mdi:water-percent-alert

      # TEMPERATURE DRIFT RATE (°C per hour estimate) - VPD v3 Compatible
      # Note: This is a simplified version. For accurate drift tracking,
      # consider using the statistics integration with mean sensor
      - name: "Temperature Drift Rate"
        unique_id: temperature_drift_rate
        unit_of_measurement: "°C/h"
        state_class: measurement
        state: >
          {% set current = states('sensor.chamber_avg_temp') | float(0) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 15 if is_pinning else 17 %}
          {% set diff = (current - target) | abs %}
          {% if diff < 0.5 %}
            0.0
          {% elif current > target %}
            {{ (diff * 0.1) | round(2) }}
          {% else %}
            {{ (-diff * 0.1) | round(2) }}
          {% endif %}
        icon: >
          {% set current = states('sensor.chamber_avg_temp') | float(0) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 15 if is_pinning else 17 %}
          {% if current > target %}
            mdi:thermometer-chevron-up
          {% elif current < target %}
            mdi:thermometer-chevron-down
          {% else %}
            mdi:thermometer
          {% endif %}
        availability: >
          {{ states('sensor.chamber_avg_temp') not in ['unavailable', 'unknown', 'none'] }}

      # ACH ACTUAL (calculated from fan state) - VPD v3 Compatible
      - name: "ACH Actual Current"
        unique_id: ach_actual_current
        unit_of_measurement: "ACH"
        state_class: measurement
        state: >
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
          {% set fan_on = is_state('switch.vifter_switch', 'on') %}
          {% if fan_on %}
            {{ target_ach }}
          {% else %}
            0.0
          {% endif %}
        icon: mdi:fan-speed-3
        availability: >
          {{ states('switch.vifter_switch') not in ['unavailable', 'unknown', 'none'] }}

      # CLIMATE HEALTH SCORE (Combined) - VPD v3 Compatible
      - name: "Climate Health Score"
        unique_id: climate_health_score
        unit_of_measurement: "%"
        state_class: measurement
        state: >
          {% set vpd_score = states('sensor.vpd_stability_score') | float(0) %}
          {% set rh_score = states('sensor.humidity_control_efficiency') | float(0) %}
          {% set temp = states('sensor.chamber_avg_temp') | float(18) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_temp = 15 if is_pinning else 17 %}
          {% set temp_diff = (temp - target_temp) | abs %}
          {% set temp_score = 100 if temp_diff < 1 else (100 - temp_diff * 20) %}
          {% set temp_score = [0, [temp_score, 100] | min] | max %}
          {{ ((vpd_score * 0.4 + rh_score * 0.4 + temp_score * 0.2) | round(0)) }}
        icon: mdi:heart-pulse

      # ─────────────────────────────────────────────────────────────────────────
      # VPD CONTROL SYSTEM SENSORS (v2.0 - Dynamisk)
      # ─────────────────────────────────────────────────────────────────────────

      # Dynamisk RH setpoint basert på temp og pinning phase
      - name: "Dynamic RH Setpoint"
        unique_id: dynamic_rh_setpoint
        unit_of_measurement: "%"
        icon: mdi:water-percent-alert
        state: >
          {% set temp = states('sensor.chamber_avg_temp') | float(18) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_vpd = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                              else states('input_number.target_vpd_fruiting') | float(0.12) %}

          {# Beregn Saturation Vapor Pressure (SVP) ved current temp #}
          {% set svp = 0.61078 * (2.71828 ** ((17.27 * temp) / (temp + 237.3))) %}

          {# Beregn nødvendig Vapor Pressure for target VPD #}
          {% set target_vp = svp - target_vpd %}

          {# Beregn RH som gir target VPD #}
          {% set rh = (target_vp / svp) * 100 %}

          {{ rh | round(1) }}
        attributes:
          temperature: "{{ states('sensor.chamber_avg_temp') | float(18) }}"
          target_vpd: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {{ states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
               else states('input_number.target_vpd_fruiting') | float(0.12) }}
          phase: "{{ 'Pinning' if is_state('input_boolean.pinning_phase', 'on') else 'Fruiting' }}"

      # RH lower/upper limits basert på VPD hysteresis
      - name: "RH Control Lower Limit"
        unique_id: rh_control_lower_limit
        unit_of_measurement: "%"
        state: >
          {% set temp = states('sensor.chamber_avg_temp') | float(18) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_vpd = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                              else states('input_number.target_vpd_fruiting') | float(0.12) %}
          {% set vpd_hyst = states('input_number.vpd_hysteresis') | float(0.03) %}

          {# Lower VPD = higher RH #}
          {% set lower_vpd = target_vpd - vpd_hyst %}
          {% set svp = 0.61078 * (2.71828 ** ((17.27 * temp) / (temp + 237.3))) %}
          {% set target_vp = svp - lower_vpd %}
          {% set rh = (target_vp / svp) * 100 %}

          {{ rh | round(1) }}

      - name: "RH Control Upper Limit"
        unique_id: rh_control_upper_limit
        unit_of_measurement: "%"
        state: >
          {% set temp = states('sensor.chamber_avg_temp') | float(18) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_vpd = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                              else states('input_number.target_vpd_fruiting') | float(0.12) %}
          {% set vpd_hyst = states('input_number.vpd_hysteresis') | float(0.03) %}

          {# Higher VPD = lower RH #}
          {% set upper_vpd = target_vpd + vpd_hyst %}
          {% set svp = 0.61078 * (2.71828 ** ((17.27 * temp) / (temp + 237.3))) %}
          {% set target_vp = svp - upper_vpd %}
          {% set rh = (target_vp / svp) * 100 %}

          {{ rh | round(1) }}

      # RH target per fase (fast temperatur 15°C/17°C, oppdateres ved VPD-target-endring)
      - name: "RH Target Pinning Phase"
        unique_id: rh_target_pinning_phase
        unit_of_measurement: "%"
        icon: mdi:water-percent
        state: >
          {% set temp = 15.0 %}
          {% set target_vpd = states('input_number.target_vpd_pinning') | float(0.10) %}
          {% set svp = 0.61078 * (2.71828 ** ((17.27 * temp) / (temp + 237.3))) %}
          {{ (((svp - target_vpd) / svp) * 100) | round(1) }}

      - name: "RH Target Fruiting Phase"
        unique_id: rh_target_fruiting_phase
        unit_of_measurement: "%"
        icon: mdi:water-percent
        state: >
          {% set temp = 17.0 %}
          {% set target_vpd = states('input_number.target_vpd_fruiting') | float(0.12) %}
          {% set svp = 0.61078 * (2.71828 ** ((17.27 * temp) / (temp + 237.3))) %}
          {{ (((svp - target_vpd) / svp) * 100) | round(1) }}

      # Status sensors
      - name: "Ventilation Status"
        unique_id: ventilation_status
        icon: >
          {% if is_state('input_boolean.ventilation_pulse_mode', 'on') %}
            mdi:fan-auto
          {% else %}
            mdi:fan-off
          {% endif %}
        state: >
          {% if is_state('input_boolean.ventilation_pulse_mode', 'on') %}
            {% if is_state('switch.vifter_switch', 'on') %}
              Pulsing (ON)
            {% elif is_state('timer.ventilation_cycle', 'active') %}
              Pulsing (OFF - {{ state_attr('timer.ventilation_cycle', 'remaining') }})
            {% else %}
              Pulse Mode Active
            {% endif %}
          {% else %}
            Manual Control
          {% endif %}
        attributes:
          on_duration: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {{ states('input_number.ventilation_on_duration_pinning' if is_pinning else 'input_number.ventilation_on_duration_fruiting') | int(120) }} s
          off_duration: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
            {% set on_sec = states('input_number.ventilation_on_duration_pinning' if is_pinning else 'input_number.ventilation_on_duration_fruiting') | int(120) %}
            {{ [(3600 / ach - on_sec) | int, 30] | max }} s
          cycle_time: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
            {{ (3600 / ach) | int }} s
          duty_cycle: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
            {% set on_sec = states('input_number.ventilation_on_duration_pinning' if is_pinning else 'input_number.ventilation_on_duration_fruiting') | int(120) %}
            {{ (on_sec / (3600 / ach) * 100) | round(1) }} %

      # ACH Calculation (Actual air changes per hour)
      # ACH Actual Calculated — ny definisjon: 1 ACH = 120s på-tid, frekvens styres av ACH-target
      - name: "ACH Actual Calculated"
        unique_id: ach_actual_calculated
        unit_of_measurement: "sykler/t"
        state_class: measurement
        icon: mdi:fan-speed-3
        state: >
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
          {% set on_sec = states('input_number.ventilation_on_duration_pinning' if is_pinning else 'input_number.ventilation_on_duration_fruiting') | int(120) %}
          {% set cycle_sec = 3600 / ach %}
          {{ (on_sec / cycle_sec * ach) | round(1) }}
        attributes:
          on_duration: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {{ states('input_number.ventilation_on_duration_pinning') if is_pinning
               else states('input_number.ventilation_on_duration_fruiting') }} s
          off_duration: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
            {% set on_sec = states('input_number.ventilation_on_duration_pinning' if is_pinning else 'input_number.ventilation_on_duration_fruiting') | int(120) %}
            {{ ((3600 / ach) - on_sec) | int }} s
          cycle_time: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set ach = states('input_number.ach_target_pinning' if is_pinning else 'input_number.ach_target_fruiting') | float(7) %}
            {{ (3600 / ach) | int }} s
          phase: "{{ 'Pinning (15°C)' if is_state('input_boolean.pinning_phase', 'on') else 'Fruiting (17°C)' }}"

      - name: "VPD Control Status"
        unique_id: vpd_control_status
        icon: mdi:chart-bell-curve
        state: >
          {% set current_vpd = states('sensor.chamber_current_vpd') | float(0) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target_vpd = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                              else states('input_number.target_vpd_fruiting') | float(0.12) %}
          {% set vpd_hyst = states('input_number.vpd_hysteresis') | float(0.03) %}
          {% set lower = target_vpd - vpd_hyst %}
          {% set upper = target_vpd + vpd_hyst %}

          {% if is_state('switch.vifter_switch', 'on') %}
            Override (Ventilation Active)
          {% elif current_vpd > upper %}
            VPD Too High ({{ current_vpd | round(2) }} > {{ upper | round(2) }})
          {% elif current_vpd < lower %}
            VPD Too Low ({{ current_vpd | round(2) }} < {{ lower | round(2) }})
          {% else %}
            VPD In Range ({{ current_vpd | round(2) }} kPa)
          {% endif %}
        attributes:
          current_vpd: "{{ states('sensor.chamber_current_vpd') | float(0) | round(2) }}"
          target_vpd: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {{ states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
               else states('input_number.target_vpd_fruiting') | float(0.12) }}
          lower_limit: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set target = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                            else states('input_number.target_vpd_fruiting') | float(0.12) %}
            {{ (target - states('input_number.vpd_hysteresis') | float(0.03)) | round(2) }}
          upper_limit: >
            {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
            {% set target = states('input_number.target_vpd_pinning') | float(0.10) if is_pinning
                            else states('input_number.target_vpd_fruiting') | float(0.12) %}
            {{ (target + states('input_number.vpd_hysteresis') | float(0.03)) | round(2) }}
          phase: "{{ 'Pinning' if is_state('input_boolean.pinning_phase', 'on') else 'Fruiting' }}"
          dynamic_rh_setpoint: "{{ states('sensor.dynamic_rh_setpoint') }}"
          current_rh: "{{ states('sensor.chamber_avg_humidity') }}"
          fogger_state: "{{ states('switch.fogger_switch') }}"

      # ─────────────────────────────────────────────────────────────────────────
      # DASHBOARD HELPER SENSORS
      # ─────────────────────────────────────────────────────────────────────────

      # Chamber Stability Index (combined score)
      - name: "Chamber Stability Index"
        unique_id: chamber_stability_index
        unit_of_measurement: "%"
        state_class: measurement
        state: >
          {% set vpd_stable = states('sensor.vpd_stability_score') | float(0) %}
          {% set health = states('sensor.climate_health_score') | float(0) %}
          {% set temp_drift = states('sensor.temperature_drift_rate') | float(0) | abs %}
          {% set temp_stable = 100 if temp_drift < 0.2 else 50 %}
          {{ ((vpd_stable * 0.5 + health * 0.3 + temp_stable * 0.2) | round(0)) }}
        icon: mdi:chart-areaspline

      # Smart Alert Status
      - name: "VPD Alert Status"
        unique_id: vpd_alert_status
        state: >
          {% set vpd = states('sensor.chamber_current_vpd') | float(0) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 0.10 if is_pinning else 0.12 %}
          {% set diff = (vpd - target) | abs %}
          {% if diff < 0.03 %}
            Perfekt
          {% elif diff < 0.08 %}
            God
          {% elif diff < 0.15 %}
            Akseptabel
          {% else %}
            Kritisk
          {% endif %}
        icon: >
          {% set vpd = states('sensor.chamber_current_vpd') | float(0) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 0.10 if is_pinning else 0.12 %}
          {% set diff = (vpd - target) | abs %}
          {% if diff < 0.03 %}
            mdi:check-circle
          {% elif diff < 0.08 %}
            mdi:check
          {% elif diff < 0.15 %}
            mdi:alert-circle-outline
          {% else %}
            mdi:alert-circle
          {% endif %}

      # Temperature Alert Status
      - name: "Temperature Alert Status"
        unique_id: temperature_alert_status
        state: >
          {% set temp = states('sensor.chamber_avg_temp') | float(18) %}
          {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
          {% set target = 15 if is_pinning else 17 %}
          {% set diff = (temp - target) | abs %}
          {% if diff < 0.5 %}
            Perfekt
          {% elif diff < 1.0 %}
            God
          {% elif diff < 2.0 %}
            Avvik
          {% else %}
            Kritisk
          {% endif %}
        icon: mdi:thermometer-alert

      # ─────────────────────────────────────────────────────────────────────────
      # SENSOR HEALTH STATUS
      # ─────────────────────────────────────────────────────────────────────────

      - name: "Sensor Health Status"
        unique_id: sensor_health_status
        state: >
          {% set sensors = [
            states('sensor.chamber_sensor_1_temperature'),
            states('sensor.chamber_sensor_2_temperature'),
            states('sensor.chamber_sensor_1_humidity')
          ] %}
          {% set unavail = sensors | select('in', ['unavailable', 'unknown', 'none']) | list | length %}
          {% set vpd_ok = states('sensor.chamber_current_vpd') not in ['unavailable', 'unknown', 'none'] %}
          {% if unavail == 0 and vpd_ok %}
            Healthy
          {% elif unavail >= 2 or not vpd_ok %}
            Critical
          {% else %}
            Degraded
          {% endif %}
        icon: >
          {% set s1_ok = states('sensor.chamber_sensor_1_temperature') not in ['unavailable', 'unknown', 'none'] %}
          {% set s2_ok = states('sensor.chamber_sensor_2_temperature') not in ['unavailable', 'unknown', 'none'] %}
          {% if s1_ok and s2_ok %}
            mdi:check-circle
          {% else %}
            mdi:alert-circle
          {% endif %}
        attributes:
          chamber_sensor_1_temp: "{{ states('sensor.chamber_sensor_1_temperature') }}"
          chamber_sensor_2_temp: "{{ states('sensor.chamber_sensor_2_temperature') }}"
          chamber_sensor_1_humidity: "{{ states('sensor.chamber_sensor_1_humidity') }}"
          vpd_sensor: "{{ states('sensor.chamber_current_vpd') }}"

      # ─────────────────────────────────────────────────────────────────────────
      # INCUBATION ROOM SENSORS (Monitoring Only - 2x Sonoff SNZB-02P)
      # ─────────────────────────────────────────────────────────────────────────

      - name: "Incubation Avg Temp"
        unique_id: incubation_avg_temp
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        icon: mdi:thermometer
        state: >
          {% set t1 = states('sensor.incubation_sensor_1_temperature') | float(none) %}
          {% set t2 = states('sensor.incubation_sensor_2_temperature') | float(none) %}
          {% set valid = [] %}
          {% if t1 is not none and t1 > 5 and t1 < 40 %}
            {% set valid = valid + [t1] %}
          {% endif %}
          {% if t2 is not none and t2 > 5 and t2 < 40 %}
            {% set valid = valid + [t2] %}
          {% endif %}
          {% if valid | length > 0 %}
            {{ (valid | sum / valid | length) | round(1) }}
          {% else %}
            unavailable
          {% endif %}
        availability: >
          {{ states('sensor.incubation_sensor_1_temperature') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.incubation_sensor_2_temperature') not in ['unavailable', 'unknown', 'none'] }}

      - name: "Incubation Avg Humidity"
        unique_id: incubation_avg_humidity
        unit_of_measurement: "%"
        device_class: humidity
        state_class: measurement
        icon: mdi:water-percent
        state: >
          {% set h1 = states('sensor.incubation_sensor_1_humidity') | float(none) %}
          {% set h2 = states('sensor.incubation_sensor_2_humidity') | float(none) %}
          {% set valid = [] %}
          {% if h1 is not none and h1 > 10 and h1 < 100 %}
            {% set valid = valid + [h1] %}
          {% endif %}
          {% if h2 is not none and h2 > 10 and h2 < 100 %}
            {% set valid = valid + [h2] %}
          {% endif %}
          {% if valid | length > 0 %}
            {{ (valid | sum / valid | length) | round(1) }}
          {% else %}
            unavailable
          {% endif %}
        availability: >
          {{ states('sensor.incubation_sensor_1_humidity') not in ['unavailable', 'unknown', 'none'] or
             states('sensor.incubation_sensor_2_humidity') not in ['unavailable', 'unknown', 'none'] }}

  # ═══════════════════════════════════════════════════════════════════════════════
  # TRIGGER-BASED RATE-OF-CHANGE SENSORS (polling every 5 min)
  # ═══════════════════════════════════════════════════════════════════════════════
  - trigger:
    - platform: time_pattern
      minutes: /5
    sensor:
      - name: "Temp Change 5min"
        unique_id: temp_change_5min
        unit_of_measurement: "°C"
        state_class: measurement
        icon: mdi:thermometer-alert
        state: >
          {% set current = states('sensor.chamber_avg_temp') | float(0) %}
          {% set previous = this.attributes.get('previous_value', current) | float(current) %}
          {{ (current - previous) | round(2) }}
        attributes:
          previous_value: "{{ states('sensor.chamber_avg_temp') | float(0) }}"
          current_value: "{{ states('sensor.chamber_avg_temp') | float(0) }}"

      - name: "Humidity Change 5min"
        unique_id: humidity_change_5min
        unit_of_measurement: "%"
        state_class: measurement
        icon: mdi:water-alert
        state: >
          {% set current = states('sensor.chamber_avg_humidity') | float(0) %}
          {% set previous = this.attributes.get('previous_value', current) | float(current) %}
          {{ (current - previous) | round(1) }}
        attributes:
          previous_value: "{{ states('sensor.chamber_avg_humidity') | float(0) }}"
          current_value: "{{ states('sensor.chamber_avg_humidity') | float(0) }}"

# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS SENSORS - 24h AVERAGES (for morgenrapport)
# ═══════════════════════════════════════════════════════════════════════════════
sensor:
  - platform: statistics
    name: "VPD 24h Mean"
    unique_id: vpd_24h_mean
    entity_id: sensor.chamber_current_vpd
    state_characteristic: mean
    max_age:
      hours: 24
    precision: 2

  - platform: statistics
    name: "Temp 24h Mean"
    unique_id: temp_24h_mean
    entity_id: sensor.chamber_avg_temp
    state_characteristic: mean
    max_age:
      hours: 24
    precision: 1

  - platform: statistics
    name: "Humidity 24h Mean"
    unique_id: humidity_24h_mean
    entity_id: sensor.chamber_avg_humidity
    state_characteristic: mean
    max_age:
      hours: 24
    precision: 1

  - platform: statistics
    name: "Health Score 24h Mean"
    unique_id: health_score_24h_mean
    entity_id: sensor.climate_health_score
    state_characteristic: mean
    max_age:
      hours: 24
    precision: 0

  - platform: statistics
    name: "VPD Stability 24h Mean"
    unique_id: vpd_stability_24h_mean
    entity_id: sensor.vpd_stability_score
    state_characteristic: mean
    max_age:
      hours: 24
    precision: 0

  - platform: history_stats
    name: "Sensor 1 offline 24h"
    unique_id: sensor_1_offline_24h
    entity_id: sensor.chamber_sensor_1_temperature
    state: unavailable
    type: time
    start: "{{ now() - timedelta(hours=24) }}"
    end: "{{ now() }}"

  - platform: history_stats
    name: "Sensor 2 offline 24h"
    unique_id: sensor_2_offline_24h
    entity_id: sensor.chamber_sensor_2_temperature
    state: unavailable
    type: time
    start: "{{ now() - timedelta(hours=24) }}"
    end: "{{ now() }}"

```

---

# automations_vpd_v3.yaml
> Alle HA-automationer

```yaml
- id: '1706189744048'
  alias: HASS Shutdown notification
  description: ''
  triggers:
  - event: shutdown
    trigger: homeassistant
  conditions: []
  actions:
  - metadata: {}
    data:
      message: HASS down!
    action: notify.mobile_app_pixel_9a
  mode: single
- id: '1706189870920'
  alias: HASS Running notification
  description: ''
  triggers:
  - event: start
    trigger: homeassistant
  conditions: []
  actions:
  - metadata: {}
    data:
      message: HASS up!
    action: notify.mobile_app_pixel_9a
  mode: single
- id: '1706464081307'
  alias: Entities offline
  description: Push når entity er unavailable
  trigger:
  - platform: state
    entity_id:
    - sensor.chamber_sensor_1_temperature
    - sensor.chamber_sensor_2_temperature
    - sensor.kammeret_humidity
    - sensor.incubation_sensor_1_temperature
    - sensor.incubation_sensor_1_humidity
    - sensor.incubation_sensor_2_temperature
    - sensor.incubation_sensor_2_humidity
    - switch.vifter_switch
    - switch.fogger_switch
    to: unavailable
    from:
  condition: []
  action:
  - service: notify.mobile_app_pixel_9a
    metadata: {}
    data:
      message: Entity offline
  mode: single
- id: '1707774861200'
  alias: Varmepumpe nattvarme
  description: Heat og fan 5 fra 0600 til 0700
  triggers:
  - at: 06:00:00
    trigger: time
  conditions:
  - condition: numeric_state
    entity_id: sensor.netatmo_ute_temperature
    below: 6
  actions:
  - metadata: {}
    data:
      fan_mode: '5'
    target:
      device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    action: climate.set_fan_mode
  - target:
      device_id:
      - 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    data:
      hvac_mode: heat
    action: climate.set_hvac_mode
  - delay:
      hours: 1
      minutes: 0
      seconds: 0
      milliseconds: 0
  - metadata: {}
    data:
      fan_mode: auto
    target:
      device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    action: climate.set_fan_mode
  - target:
      device_id:
      - 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    data:
      hvac_mode: fan_only
    enabled: false
    action: climate.set_hvac_mode
  mode: single
- id: '1726261596303'
  alias: Sofalys av ved Shield på
  description: ''
  triggers:
  - device_id: 970ec9f159904a94a72d554904570211
    domain: media_player
    entity_id: 81f173bca31b10feee7561d004cee1d1
    type: playing
    trigger: device
    for:
      hours: 0
      minutes: 0
      seconds: 5
  conditions: []
  actions:
  - type: turn_off
    device_id: 2fd63bcc76d641701747a4b22e965745
    entity_id: 9708f5dc00642cdfcd7fbb1a522e2487
    domain: light
  mode: single
- id: '1726826102874'
  alias: Auto varme under 16 grader
  description: ''
  triggers:
  - type: temperature
    device_id: cd64aaaeb40b5c949c2f55ab5388c604
    entity_id: 39fc0024d5bc2f88a38186fb6b4bb196
    domain: sensor
    below: 16
    for:
      hours: 0
      minutes: 0
      seconds: 10
    trigger: device
  conditions: []
  actions:
  - metadata: {}
    data: {}
    target:
      device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    action: climate.turn_on
  - target:
      device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    data:
      hvac_mode: heat
      temperature: 20
    action: climate.set_temperature
  - metadata: {}
    data:
      fan_mode: Auto
    target:
      device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    action: climate.set_fan_mode
  mode: single
- id: '1726842316112'
  alias: Auto off climate 16 grader
  description: ''
  trigger:
  - type: temperature
    platform: device
    device_id: cd64aaaeb40b5c949c2f55ab5388c604
    entity_id: 39fc0024d5bc2f88a38186fb6b4bb196
    domain: sensor
    above: 16
    for:
      hours: 0
      minutes: 0
      seconds: 10
  condition: []
  action:
  - target:
      device_id:
      - 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    data: {}
    action: climate.turn_off
  mode: single
- id: '1732612893605'
  alias: Sanna i fallet
  description: Send notifikasjon raskt når Sanna kommer hjem til Lorenfallet.
  triggers:
  - entity_id: person.sanna
    from: not_home
    to: zone.lorenfallet
    trigger: state
  conditions:
  - condition: zone
    entity_id: person.aasmund
    zone: zone.lorenfallet
  actions:
  - data:
      message: Sanna hjemme
      title: Hjemkomst
      data:
        priority: high
        ttl: 0
    action: notify.mobile_app_pixel_9a
  mode: single
- id: '1733942854591'
  alias: Panelovn hos Nils – ukedager og helg
  description: ''
  triggers:
  - trigger: time
    at: '15:00:00'
    id: weekday_on
  - trigger: time
    at: 08:00:00
    id: weekend_on
  - trigger: time
    at: '19:00:00'
    id: 'off'
  conditions: []
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: weekday_on
      - condition: time
        weekday:
        - mon
        - tue
        - wed
        - thu
        - fri
      sequence:
      - device_id: 58ce76ef1fcdf966289b9019de433399
        domain: climate
        entity_id: 2deebe9c8ee5fb72a9cdebcd93864df1
        type: set_hvac_mode
        hvac_mode: heat
    - conditions:
      - condition: trigger
        id: weekend_on
      - condition: time
        weekday:
        - sat
        - sun
      sequence:
      - device_id: 58ce76ef1fcdf966289b9019de433399
        domain: climate
        entity_id: 2deebe9c8ee5fb72a9cdebcd93864df1
        type: set_hvac_mode
        hvac_mode: heat
    - conditions:
      - condition: trigger
        id: 'off'
      sequence:
      - device_id: 58ce76ef1fcdf966289b9019de433399
        domain: climate
        entity_id: 2deebe9c8ee5fb72a9cdebcd93864df1
        type: set_hvac_mode
        hvac_mode: 'off'
  mode: single
- id: '1734530682780'
  alias: Bil lader ikke
  description: Slår av lading hjemme mellom 07.00 og 20.00
  triggers:
  - type: plugged_in
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: 427c60f650bcef73514565197e548103
    domain: binary_sensor
    trigger: device
  conditions:
  - condition: time
    after: 07:00:00
    before: '19:59:59'
  - condition: zone
    entity_id: device_tracker.skoda_enyaq_position
    zone: zone.home
  actions:
  - type: turn_off
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: cfcde504ac687a9af5150274ed56c912
    domain: switch
  mode: single
- id: '1734531029313'
  alias: Billader slås på kl 20.00
  description: Slås på kl 20.00 og av kl 07.00
  triggers:
  - trigger: time
    at: '20:00:00'
  conditions:
  - condition: zone
    entity_id: device_tracker.skoda_enyaq_position
    zone: zone.home
  - type: is_plugged_in
    condition: device
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: 427c60f650bcef73514565197e548103
    domain: binary_sensor
  actions:
  - type: turn_on
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: cfcde504ac687a9af5150274ed56c912
    domain: switch
  mode: single
- id: '1745505027445'
  alias: Lading slår seg av kl 07.00
  description: Slås av kl 07.00 på hverdager
  triggers:
  - trigger: time
    at: 07:00:00
  conditions:
  - condition: zone
    entity_id: device_tracker.skoda_enyaq_position
    zone: zone.home
  - condition: time
    weekday:
    - mon
    - tue
    - wed
    - thu
    - fri
  - type: is_plugged_in
    condition: device
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: 427c60f650bcef73514565197e548103
    domain: binary_sensor
  actions:
  - type: turn_off
    device_id: 8724b81100207b9d13d54087e9e3cbe7
    entity_id: cfcde504ac687a9af5150274ed56c912
    domain: switch
  mode: single
- id: '1756930475959'
  alias: Varmepumpe kun vifte over 22 grader
  description: ''
  triggers:
  - type: temperature
    device_id: edc4bc0ae8613f7a4a0eb8e6b39a5684
    entity_id: 1a1ac297c5e0035fc948b72bef8668c2
    domain: sensor
    trigger: device
    above: 22
    for:
      hours: 0
      minutes: 2
      seconds: 0
  conditions:
  - condition: device
    device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    domain: climate
    entity_id: 23360e47581908809e5063665e22e912
    type: is_hvac_mode
    hvac_mode: heat
  actions:
  - device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    domain: climate
    entity_id: 23360e47581908809e5063665e22e912
    type: set_hvac_mode
    hvac_mode: fan_only
  mode: single
- id: '1757947818341'
  alias: Varmepumpe slår på heat under 22 grader
  description: ''
  triggers:
  - type: temperature
    device_id: edc4bc0ae8613f7a4a0eb8e6b39a5684
    entity_id: 1a1ac297c5e0035fc948b72bef8668c2
    domain: sensor
    trigger: device
    for:
      hours: 0
      minutes: 2
      seconds: 0
    below: 22
  conditions:
  - condition: device
    device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    domain: climate
    entity_id: 23360e47581908809e5063665e22e912
    type: is_hvac_mode
    hvac_mode: fan_only
  actions:
  - device_id: 7eedb8b9df0896ee5b6b64dd3fa6ebe6
    domain: climate
    entity_id: 23360e47581908809e5063665e22e912
    type: set_hvac_mode
    hvac_mode: heat
  mode: single
- id: '1763482457315'
  alias: Varmepumpe kun oppvarming (Netatmo)
  description: 'Styrer varmepumpe kun for oppvarming.  Inkluderer sikkerhetssjekk:
    Stopper hvis Netatmo ikke har oppdatert seg på 30 min.

    '
  triggers:
  - entity_id:
    - sensor.netatmo_inne_temperature
    - input_number.onsket_innetemp
    trigger: state
  - minutes: /15
    trigger: time_pattern
  conditions:
  - condition: template
    value_template: '{{ states(''sensor.netatmo_inne_temperature'') not in [''unknown'',
      ''unavailable'', ''none''] }}'
  - condition: template
    value_template: '{{ (now() - states.sensor.netatmo_inne_temperature.last_updated).total_seconds()
      < 1800 }}'
  - condition: template
    value_template: '{{ (now() - states.climate.varmepumpe.last_changed).total_seconds()
      > 900 }}'
  actions:
  - variables:
      actual: '{{ states(''sensor.netatmo_inne_temperature'') | float(20) }}'
      target: '{{ states(''input_number.onsket_innetemp'') | float(22) }}'
      outdoor: '{{ states(''sensor.netatmo_ute_temperature'') | float(5) }}'
      current_hvac: '{{ states(''climate.varmepumpe'') }}'
      diff: '{{ target - actual }}'
      outdoor_factor: '{{ 1.0 + ((5.0 - outdoor) * 0.02) }}'
      min_temp: 18
      max_temp: 26
  - variables:
      calculated_temp: '{{ ([target | round(0), min_temp] | max) if diff < -0.4 else
        ([(target + diff + 0.5 * outdoor_factor) | round(0), max_temp] | min) if diff
        > 0.4 else (actual | round(0)) }}'
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ diff >= -0.4 and diff <= 0.4 }}'
      sequence: []
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ current_hvac != ''heat'' }}'
      sequence:
      - target:
          entity_id: climate.varmepumpe
        data:
          hvac_mode: heat
        action: climate.set_hvac_mode
  - target:
      entity_id: climate.varmepumpe
    data:
      temperature: '{{ calculated_temp | float }}'
    action: climate.set_temperature
  - target:
      entity_id: climate.varmepumpe
    data:
      fan_mode: '{{ ''5'' if diff > 1.5 else ''4'' if diff > 1 else ''auto'' }}'
    action: climate.set_fan_mode
  mode: single
- id: '1764247559363'
  alias: Notifikasjon - Varmepumpeinnstilling endret
  description: Sender varsel når varmepumpens setpunkt eller modus endres.
  triggers:
  - trigger: state
    entity_id: climate.varmepumpe
    attribute: temperature
  - trigger: state
    entity_id: climate.varmepumpe
    attribute: fan_mode
  - trigger: state
    entity_id: climate.varmepumpe
    attribute: hvac_mode
  conditions: []
  actions:
  - variables:
      new_temp: '{{ state_attr(''climate.varmepumpe'', ''temperature'') }}'
      new_fan: '{{ state_attr(''climate.varmepumpe'', ''fan_mode'') }}'
      new_hvac: '{{ state_attr(''climate.varmepumpe'', ''hvac_mode'') }}'
      old_temp: '{{ trigger.from_state.attributes.temperature }}'
      old_fan: '{{ trigger.from_state.attributes.fan_mode }}'
      old_hvac: '{{ trigger.from_state.attributes.hvac_mode }}'
      message_body: "{% set changes = [] %} {% if new_hvac != old_hvac %}\n  {% set
        changes = changes + [\"Modus: \" ~ old_hvac ~ \" -> \" ~ new_hvac] %}\n{%
        endif %} {% if new_temp != old_temp %}\n  {% set changes = changes + [\"Setpunkt:
        \" ~ old_temp ~ \"°C -> \" ~ new_temp ~ \"°C\"] %}\n{% endif %} {% if new_fan
        != old_fan %}\n  {% set changes = changes + [\"Vifte: \" ~ old_fan ~ \" ->
        \" ~ new_fan] %}\n{% endif %} Varmepumpen har endret innstilling. Endringer:
        {{ changes | join(', ') }}\n"
  - data:
      title: "\U0001F525 Varmepumpe Justering"
      message: '{{ message_body }}'
      data:
        priority: high
        channel: Varmepumpe
    action: notify.mobile_app_pixel_9a
  mode: single
- id: '1764859108898'
  alias: Varme i Evelina sitt rom automatisk
  description: ''
  triggers:
  - entity_id: person.evelina
    trigger: state
  actions:
  - choose:
    - conditions:
      - condition: state
        entity_id: person.evelina
        state: home
      sequence:
      - target:
          entity_id: climate.evelina_900w
        data:
          hvac_mode: heat
        action: climate.set_hvac_mode
    - conditions:
      - condition: state
        entity_id: person.evelina
        state: not_home
      sequence:
      - target:
          entity_id: climate.evelina_900w
        data:
          hvac_mode: 'off'
        action: climate.set_hvac_mode
  mode: single
- id: '1765131298558'
  alias: VVB av over 10Kw
  description: Slår av Aeotec Heavy Duty når huset bruker over 10kW i 5 minutter
  triggers:
  - entity_id: sensor.tibber_pulse_samlevegen_17_power
    above: 10000
    for:
      minutes: 5
    trigger: numeric_state
  conditions: []
  actions:
  - target:
      entity_id: switch.aeotec_heavy_duty_switch
    action: switch.turn_off
  mode: single
- id: '1765131346958'
  alias: VVB på når forbruket er under 7kW
  description: Slår på Aeotec Heavy Duty når forbruket går under 7kW i 2 minutter
  triggers:
  - entity_id: sensor.tibber_pulse_samlevegen_17_power
    below: 7000
    for:
      minutes: 2
    trigger: numeric_state
  conditions:
  - condition: state
    entity_id: switch.aeotec_heavy_duty_switch
    state: 'off'
  actions:
  - target:
      entity_id: switch.aeotec_heavy_duty_switch
    action: switch.turn_on
  mode: single
- alias: Chamber - Maximum RH Safety
  description: Emergency stop at 98% RH to prevent condensation
  mode: single
  trigger:
  - platform: numeric_state
    entity_id: sensor.chamber_avg_humidity
    above: 98
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: switch.turn_off
    target:
      entity_id: switch.fogger_switch
  - service: persistent_notification.create
    data:
      title: '⚠️ HIGH ALARM: RH Too High'
      message: 'Humidity at {{ states(''sensor.chamber_avg_humidity'') }}% -  humidifier
        stopped. Check ventilation!

        '
      notification_id: high_rh_alarm
  id: 8a37d4381ae74998aaa32f4492e9993c
- id: ventilation_timer_v4
  alias: 'Ventilation: Timer-Based Cycle'
  description: >
    1 ACH = 120s på-tid = én komplett luftutskifting (empirisk målt).
    ACH-target styrer frekvens (n ganger per time). Off-tid: (3600/ACH) - on_duration sekunder.
  trigger:
  - platform: event
    event_type: timer.finished
    event_data:
      entity_id: timer.ventilation_cycle
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: switch.turn_on
    target:
      entity_id: switch.vifter_switch
  - delay:
      seconds: >
        {% if is_state('input_boolean.pinning_phase', 'on') %}
          {{ states('input_number.ventilation_on_duration_pinning') | int }}
        {% else %}
          {{ states('input_number.ventilation_on_duration_fruiting') | int }}
        {% endif %}
  - service: switch.turn_off
    target:
      entity_id: switch.vifter_switch
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: >
        {% set ach_entity = 'input_number.ach_target_pinning' if is_state('input_boolean.pinning_phase', 'on') else 'input_number.ach_target_fruiting' %}
        {% set on_entity = 'input_number.ventilation_on_duration_pinning' if is_state('input_boolean.pinning_phase', 'on') else 'input_number.ventilation_on_duration_fruiting' %}
        {% set ach = states(ach_entity) | float(7) %}
        {% set on_sec = states(on_entity) | int(120) %}
        {% set off_sec = ((3600 / ach) - on_sec) | int %}
        {{ [off_sec, 30] | max }}
  mode: single
- id: ventilation_pulse_stop_v2
  alias: 'Ventilation: Stop Pulse Cycle (VPD)'
  description: Stopper ventilasjons-pulssyklusen når pulse mode deaktiveres
  trigger:
  - platform: state
    entity_id: input_boolean.ventilation_pulse_mode
    to: 'off'
  action:
  - service: timer.cancel
    target:
      entity_id: timer.ventilation_cycle
  - service: switch.turn_off
    target:
      entity_id:
      - switch.vifter_switch
  mode: single
- id: ventilation_pulse_start
  alias: 'Ventilation: Start Pulse Cycle'
  description: Starter timer.ventilation_cycle når systemet aktiveres (pulse_mode → on). Slår også på lys i dagtid.
  trigger:
  - platform: state
    entity_id: input_boolean.ventilation_pulse_mode
    to: 'on'
  action:
  - delay:
      seconds: 5
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: "0:00:05"
  - condition: time
    after: '06:00:00'
    before: '18:00:00'
  - service: light.turn_on
    target:
      entity_id: light.fruktenkammer
  mode: single
- id: vpd_control_fogger_burst_v3
  alias: 'VPD Control: Fogger Burst (60s Time Pattern)'
  description: 14s fogger burst hvert minutt når VPD er for høy (23% duty cycle)
  trigger:
  - platform: time_pattern
    minutes: /1
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: template
    value_template: >
      {% set vpd_raw = states('sensor.chamber_current_vpd') %}
      {% if vpd_raw in ['unknown', 'unavailable'] %}
        {{ False }}
      {% else %}
        {% set vpd = vpd_raw | float(0) %}
        {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
        {% set target_vpd = states('input_number.target_vpd_pinning' if is_pinning else 'input_number.target_vpd_fruiting') | float(0.12) %}
        {% set hyst = states('input_number.vpd_hysteresis') | float(0.02) %}
        {{ vpd >= (target_vpd + hyst) }}
      {% endif %}
  action:
  - service: switch.turn_on
    target:
      entity_id: switch.fogger_switch
  - delay:
      seconds: 14
  - service: switch.turn_off
    target:
      entity_id: switch.fogger_switch
  mode: single
- id: vpd_fog_after_ventilation
  alias: 'VPD Control: Fog After Ventilation'
  description: Proaktiv fogger-burst rett etter at viften slår av — kompenserer for
    humidity-drop fra ventilasjon UMIDDELBART istedenfor å vente på sensor-rapportering
  trigger:
  - platform: state
    entity_id: switch.vifter_switch
    to: 'off'
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: state
    entity_id: switch.fogger_switch
    state: 'off'
  - condition: template
    value_template: >
      {% set vpd_raw = states('sensor.chamber_current_vpd') %}
      {% if vpd_raw in ['unknown', 'unavailable'] %}
        {{ False }}
      {% else %}
        {% set vpd = vpd_raw | float(0) %}
        {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
        {% set target_vpd = states('input_number.target_vpd_pinning' if is_pinning else 'input_number.target_vpd_fruiting') | float(0.12) %}
        {{ vpd >= target_vpd }}
      {% endif %}
  action:
  - service: switch.turn_on
    target:
      entity_id: switch.fogger_switch
  - delay:
      seconds: 14
  - service: switch.turn_off
    target:
      entity_id: switch.fogger_switch
  mode: single
- id: vpd_control__emergency_stop_v3
  alias: 'VPD Control: Emergency Stop Fogger'
  description: Stopper fogger umiddelbart hvis VPD normaliseres under burst/cooldown
  triggers:
  - trigger: template
    value_template: >
      {% set vpd = states('sensor.chamber_current_vpd') | float(999) %}
      {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
      {% set target_vpd = states('input_number.target_vpd_pinning' if is_pinning else 'input_number.target_vpd_fruiting') | float(0.12) %}
      {% set hyst = states('input_number.vpd_hysteresis') | float(0.02) %}
      {{ vpd < (target_vpd - hyst) }}
  conditions:
  - condition: state
    entity_id: switch.fogger_switch
    state: 'on'
  actions:
  - target:
      entity_id: switch.fogger_switch
    action: switch.turn_off
  mode: single
- id: 'sopp_tracker_frontend_autostart'
  alias: 'Sopp Tracker: Auto-start frontend ved HASS oppstart'
  description: Starter Sopp Tracker frontend automatisk når Home Assistant restarter
  triggers:
  - event: start
    trigger: homeassistant
  conditions: []
  actions:
  - delay:
      seconds: 30
  - service: shell_command.start_sopp_frontend
  - service: persistent_notification.create
    data:
      title: '🍄 Sopp Tracker Frontend Started'
      message: 'Sopp Tracker frontend is now running on http://192.168.1.251:3001'
      notification_id: sopp_tracker_frontend_start
  mode: single
- id: 'vpd_critical_alert_mobile'
  alias: 'VPD Alert: Critical VPD Mobile Notification'
  description: Sender push til mobil når VPD er kritisk høy i 15 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.chamber_current_vpd
    above: 0.35
    for:
      minutes: 15
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ VPD Kritisk Høy!'
      message: 'VPD er {{ states(''sensor.chamber_current_vpd'') }} kPa i 15 minutter. Sjekk fogger og ventilasjon!'
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: 'climate_health_critical_alert'
  alias: 'VPD Alert: Climate Health Critical'
  description: Varsler når Climate Health Score er under 30% i 30 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.climate_health_score
    below: 30
    for:
      minutes: 30
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: '🚨 Climate Health Kritisk!'
      message: 'Climate Health er {{ states(''sensor.climate_health_score'') }}%. VPD: {{ states(''sensor.chamber_current_vpd'') }} kPa'
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: 'fogger_not_responding_alert'
  alias: 'VPD Alert: Fogger Not Responding'
  description: Varsler hvis VPD forblir høy selv om foggeren kjører
  trigger:
  - platform: numeric_state
    entity_id: sensor.chamber_current_vpd
    above: 0.30
    for:
      minutes: 60
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Fogger Mulig Feil'
      message: 'VPD fortsatt {{ states(''sensor.chamber_current_vpd'') }} kPa etter 60 min. Sjekk vannivå/dyse!'
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: fogger_inactivity_alert
  alias: 'VPD Alert: Fogger Inaktiv 30 min'
  description: Varsler hvis foggeren ikke har slått seg på på 30 minutter OG VPD er over mål — forhindrer falsk alarm når VPD er bra
  trigger:
  - platform: state
    entity_id: switch.fogger_switch
    to: 'off'
    for:
      minutes: 30
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: template
    value_template: >
      {% set vpd_raw = states('sensor.chamber_current_vpd') %}
      {% if vpd_raw in ['unknown', 'unavailable'] %}
        {{ False }}
      {% else %}
        {% set vpd = vpd_raw | float(0) %}
        {% set is_pinning = is_state('input_boolean.pinning_phase', 'on') %}
        {% set target = states('input_number.target_vpd_pinning' if is_pinning else 'input_number.target_vpd_fruiting') | float(0.12) %}
        {{ vpd > target }}
      {% endif %}
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Fogger inaktiv'
      message: >
        Foggeren har ikke slått seg på på 30+ minutter, men VPD er høy.
        Nåværende VPD: {{ states('sensor.chamber_current_vpd') }} kPa
        (Mål: {{ states('input_number.target_vpd_fruiting') }} kPa).
        Sjekk VPD-automasjon og Zigbee-tilkobling!
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: fan_inactivity_alert
  alias: 'VPD Alert: Vifte Inaktiv for lenge'
  description: Varsler hvis ventilasjonsviften ikke har slått seg på utover forventet ACH-intervall
  trigger:
  - platform: state
    entity_id: switch.vifter_switch
    to: 'off'
    for:
      minutes: 35
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: template
    value_template: >
      {% set ach = states('input_number.ach_target_pinning' if
                   is_state('input_boolean.pinning_phase', 'on')
                   else 'input_number.ach_target_fruiting') | float(7) %}
      {% set expected_max_off = ((3600 / ach) - 120 + 90) | int %}
      {{ (now() - states.switch.vifter_switch.last_changed).total_seconds() > expected_max_off }}
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Vifte inaktiv'
      message: >
        Ventilasjonsviften har ikke slått seg på på over
        {{ ((3600 / (states('input_number.ach_target_fruiting') | float(7)) - 120 + 90) / 60) | int }} min.
        (Forventet intervall ved ACH {{ states('input_number.ach_target_fruiting') | int }}: ~{{ (3600 / (states('input_number.ach_target_fruiting') | float(7)) / 60) | int }} min)
        Sjekk ventilation_timer_v4 og Zigbee-tilkobling!
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
# ═══════════════════════════════════════════════════════════════════════════════
# PINNING PHASE 48H AUTO-RETURN
# ═══════════════════════════════════════════════════════════════════════════════
- id: 'pinning_timer_start'
  alias: 'Pinning: Start 48h Auto-Return Timer'
  description: Starter 48-timers nedtelling når pinning phase aktiveres
  trigger:
  - platform: state
    entity_id: input_boolean.pinning_phase
    to: 'on'
  condition: []
  action:
  - service: timer.start
    target:
      entity_id: timer.pinning_phase_countdown
    data:
      duration: "48:00:00"
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'Pinning Phase Aktivert'
      message: >
        Pinning phase startet. Automatisk retur til fruiting om 48 timer.
        VPD Target: {{ states('input_number.target_vpd_pinning') }} kPa | Temp: 15°C | Ventilasjon: 120s, ACH {{ states('input_number.ach_target_pinning') | int }}
      data:
        priority: normal
        channel: VPD_Phase
  mode: single
- id: 'pinning_timer_finished'
  alias: 'Pinning: Auto-Return to Fruiting After 48h'
  description: Bytter automatisk tilbake til fruiting når 48-timers nedtelling er ferdig
  trigger:
  - platform: event
    event_type: timer.finished
    event_data:
      entity_id: timer.pinning_phase_countdown
  condition:
  - condition: state
    entity_id: input_boolean.pinning_phase
    state: 'on'
  action:
  - service: input_boolean.turn_off
    target:
      entity_id: input_boolean.pinning_phase
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'Pinning Fullfort - Fruiting Aktivert'
      message: >
        48-timers pinning phase fullfort. System automatisk byttet til fruiting.
        Nye innstillinger: VPD {{ states('input_number.target_vpd_fruiting') }} kPa | Temp: 17°C | Ventilasjon: 120s, ACH {{ states('input_number.ach_target_fruiting') | int }}
      data:
        priority: high
        channel: VPD_Phase
        actions:
        - action: "URI"
          title: "Se Dashboard"
          uri: "/lovelace/vpd-climate"
  mode: single
- id: 'pinning_timer_cancel'
  alias: 'Pinning: Kanseller Timer ved Manuell Bytte'
  description: Kansellerer nedtelling hvis bruker manuelt bytter til fruiting
  trigger:
  - platform: state
    entity_id: input_boolean.pinning_phase
    to: 'off'
  condition:
  - condition: state
    entity_id: timer.pinning_phase_countdown
    state: 'active'
  action:
  - service: timer.cancel
    target:
      entity_id: timer.pinning_phase_countdown
  mode: single
# ═══════════════════════════════════════════════════════════════════════════════
# SENSOR ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
- id: 'anomaly_temperature_rapid_change'
  alias: 'Anomaly: Rask Temperaturendring'
  description: Varsler når temperaturen endrer seg mer enn 1°C på 5 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.temp_change_5min
    above: 1.0
    for:
      minutes: 1
  - platform: numeric_state
    entity_id: sensor.temp_change_5min
    below: -1.0
    for:
      minutes: 1
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'Temperatur Anomali'
      message: >
        Temperatur endret seg {{ states('sensor.temp_change_5min') }}°C siste 5 min.
        Nåværende: {{ states('sensor.chamber_avg_temp') }}°C
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: 'anomaly_humidity_rapid_change'
  alias: 'Anomaly: Rask Fuktighetsendring'
  description: Varsler når fuktighet endrer seg mer enn 5% på 5 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.humidity_change_5min
    above: 5.0
    for:
      minutes: 1
  - platform: numeric_state
    entity_id: sensor.humidity_change_5min
    below: -5.0
    for:
      minutes: 1
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'Fuktighets Anomali'
      message: >
        Fuktighet endret seg {{ states('sensor.humidity_change_5min') }}% siste 5 min.
        Nåværende: {{ states('sensor.chamber_avg_humidity') }}%
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: 'anomaly_sensor_offline'
  alias: 'Anomaly: Sensor Offline'
  description: Varsler når sensorer er offline i mer enn 2-5 minutter
  trigger:
  - platform: state
    entity_id: sensor.sensor_health_status
    to: 'Critical'
    for:
      minutes: 2
  - platform: state
    entity_id: sensor.sensor_health_status
    to: 'Degraded'
    for:
      minutes: 5
  condition: []
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'Sensor Problem'
      message: >
        Sensor health: {{ states('sensor.sensor_health_status') }}
        S1: {{ states('sensor.chamber_sensor_1_temperature') }}°C / {{ states('sensor.chamber_sensor_1_humidity') }}%
        S2: {{ states('sensor.chamber_sensor_2_temperature') }}°C
        VPD: {{ states('sensor.chamber_current_vpd') }}
        Sjekk sensor tilkoblinger!
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: 'anomaly_temperature_out_of_range'
  alias: 'Anomaly: Temperatur Utenfor Område'
  description: Varsler når temperatur er under 14°C eller over 20°C i 5 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.chamber_avg_temp
    above: 20
    for:
      minutes: 5
  - platform: numeric_state
    entity_id: sensor.chamber_avg_temp
    below: 14
    for:
      minutes: 5
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'KRITISK: Temperatur Utenfor Område'
      message: >
        Temperatur er {{ states('sensor.chamber_avg_temp') }}°C - utenfor trygt område (14-20°C).
        Sjekk klimakontroll umiddelbart!
      data:
        priority: high
        channel: VPD_Critical
        actions:
        - action: "URI"
          title: "Se Dashboard"
          uri: "/lovelace/vpd-climate"
  mode: single
- id: 'anomaly_humidity_out_of_range'
  alias: 'Anomaly: Fuktighet Utenfor Område'
  description: Varsler når fuktighet er over 97% eller under 60% i 10 minutter
  trigger:
  - platform: numeric_state
    entity_id: sensor.chamber_avg_humidity
    above: 97
    for:
      minutes: 10
  - platform: numeric_state
    entity_id: sensor.chamber_avg_humidity
    below: 60
    for:
      minutes: 10
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'KRITISK: Fuktighet Utenfor Område'
      message: >
        Fuktighet er {{ states('sensor.chamber_avg_humidity') }}%.
        {% if states('sensor.chamber_avg_humidity') | float > 97 %}
        Risiko for kondens! Øk ventilasjon.
        {% else %}
        For tørt! Sjekk fogger og vannivå.
        {% endif %}
      data:
        priority: high
        channel: VPD_Critical
  mode: single
# ═══════════════════════════════════════════════════════════════════════════════
# DAILY MORNING STATUS REPORT
# ═══════════════════════════════════════════════════════════════════════════════
- id: 'daily_morning_status_report'
  alias: 'VPD: Daglig Morgenrapport'
  description: Sender VPD-systemstatus til mobil hver morgen kl 08:00
  trigger:
  - platform: time
    at: "08:00:00"
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'VPD Rapport {{ now().strftime("%d.%m") }}'
      message: >
        {% set health = states('sensor.health_score_24h_mean') | float(0) %}
        {% if health >= 90 %}Systemet fungerer utmerket.
        {% elif health >= 70 %}Systemet fungerer greit, men kan justeres.
        {% else %}Systemet trenger oppmerksomhet!
        {% endif %}
        Helse: {{ states('sensor.health_score_24h_mean') }}% | Stabilitet: {{ states('sensor.vpd_stability_24h_mean') }}%

        — Snitt siste 24t —
        VPD: {{ states('sensor.vpd_24h_mean') }} kPa (mål: {{ '0.10' if is_state('input_boolean.pinning_phase', 'on') else '0.12' }})
        Temp: {{ states('sensor.temp_24h_mean') }}°C
        RH: {{ states('sensor.humidity_24h_mean') }}% (mål: {{ states('sensor.dynamic_rh_setpoint') }}%)

        {{ 'Pinning (15°C)' if is_state('input_boolean.pinning_phase', 'on') else 'Fruiting (17°C)' }}
        {% if is_state('input_boolean.pinning_phase', 'on') and is_state('timer.pinning_phase_countdown', 'active') %}
        Pinning gjenstar: {{ state_attr('timer.pinning_phase_countdown', 'remaining') }}
        {% endif %}

        {% set s1_off = states('sensor.sensor_1_offline_24h') | float(0) %}
        {% set s2_off = states('sensor.sensor_2_offline_24h') | float(0) %}
        {% if states('sensor.sensor_health_status') != 'Healthy' or s1_off > 0 or s2_off > 0 %}
        Sensorer: {{ states('sensor.sensor_health_status') }}{% if s1_off > 0 %} (S1 offline {{ s1_off | round(1) }}t){% endif %}{% if s2_off > 0 %} (S2 offline {{ s2_off | round(1) }}t){% endif %}
        {% endif %}
      data:
        priority: normal
        channel: VPD_Daily
        actions:
        - action: "URI"
          title: "Se Dashboard"
          uri: "/lovelace/vpd-climate"
  mode: single
# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY AUTOMATIONS (imported from legacy automations.yaml)
# ═══════════════════════════════════════════════════════════════════════════════
- id: fogger_watchdog_safety
  alias: 'Fogger Watchdog: Safety Shutoff'
  description: Slår av fogger automatisk hvis den står på lengre enn 30 sekunder
  trigger:
  - platform: state
    entity_id: switch.fogger_switch
    to: 'on'
    for:
      seconds: 30
  action:
  - service: switch.turn_off
    target:
      entity_id: switch.fogger_switch
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Fogger Watchdog'
      message: 'Fogger ble automatisk slått AV etter 30s. Sjekk VPD automation!'
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: fan_watchdog_safety
  alias: 'Fan Watchdog: Safety Shutoff'
  description: >
    Slår av ventilasjonsviften automatisk hvis den har stått på lengre enn 150s
    (failsafe - normal on_duration 120s + 30s margin). Restarter også
    timer.ventilation_cycle slik at ventilasjonssyklusen ikke stopper permanent.
  trigger:
  - platform: state
    entity_id: switch.vifter_switch
    to: 'on'
    for:
      seconds: 150
  action:
  - service: switch.turn_off
    target:
      entity_id: switch.vifter_switch
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Fan Watchdog utløst'
      message: 'Ventilasjonsviften ble automatisk slått AV etter 150s (watchdog). Ventilasjonssyklus fortsetter. Sjekk ventilation_timer_v4!'
      data:
        priority: high
        channel: VPD_Alerts
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: >
        {% set ach_entity = 'input_number.ach_target_pinning' if is_state('input_boolean.pinning_phase', 'on') else 'input_number.ach_target_fruiting' %}
        {% set on_entity = 'input_number.ventilation_on_duration_pinning' if is_state('input_boolean.pinning_phase', 'on') else 'input_number.ventilation_on_duration_fruiting' %}
        {% set ach = states(ach_entity) | float(7) %}
        {% set on_sec = states(on_entity) | int(120) %}
        {% set off_sec = ((3600 / ach) - on_sec) | int %}
        {{ [off_sec, 30] | max }}
  mode: single
- id: ventilation_timer_idle_watchdog
  alias: 'Ventilation: Timer Idle Watchdog (Lag 3)'
  description: >
    Evighetsmaskin-recovery: restarter timer.ventilation_cycle hvis den har vært idle
    i 30 minutter mens ventilation_pulse_mode er ON. Normal idle-tid er ~120s (fan ON-periode),
    så 30 min er 14× normalverdi — aldri falske positiver. Timer settes til 30s slik at
    ventilation_timer_v4 tar over og kjører normal fan-syklus. Sikrer at ventilasjon
    aldri stopper permanent uansett intern HA-feil.
  trigger:
  - platform: state
    entity_id: timer.ventilation_cycle
    to: idle
    for:
      minutes: 30
  condition:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  action:
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: "00:00:30"
  - service: notify.mobile_app_pixel_9a
    data:
      title: '⚠️ Ventilasjon gjenopprettet automatisk'
      message: >
        timer.ventilation_cycle hadde stoppet (idle >30 min). Automatisk gjenstart
        kl {{ now().strftime('%H:%M') }}. Sjekk HA-logger for rotårsak.
      data:
        priority: high
        channel: VPD_Alerts
  mode: single
- id: safety_fan_off_on_ha_start
  alias: 'Safety: Fan Off on HA Start'
  description: >
    Sikrer at ventilasjonsviften og foggeren er AV ved HA-omstart.
    Starter ventilasjonstimeren etter 90s kun hvis alle sensorer er online
    (sensor-sjekk håndteres av startup_sensor_availability_check).
  trigger:
  - platform: homeassistant
    event: start
  action:
  - service: switch.turn_off
    target:
      entity_id:
      - switch.vifter_switch
      - switch.fogger_switch
  - delay:
      seconds: 90
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: "0:00:05"
  mode: single

- id: startup_sensor_availability_check
  alias: 'Safety: Sensor Check ved Oppstart'
  description: >
    Sjekker at alle kammer-sensorer er online 85s etter oppstart.
    Blokkerer VPD-systemet og varsler mobil hvis noen sensorer mangler.
    Kjører FØR safety_fan_off_on_ha_start starter timeren (90s).
  trigger:
  - platform: homeassistant
    event: start
  action:
  - delay:
      seconds: 85
  - variables:
      s1t: "{{ states('sensor.chamber_sensor_1_temperature') }}"
      s1h: "{{ states('sensor.chamber_sensor_1_humidity') }}"
      s2t: "{{ states('sensor.chamber_sensor_2_temperature') }}"
      s2h: "{{ states('sensor.chamber_sensor_2_humidity') }}"
  - variables:
      offline_list: >
        {% set ns = namespace(items=[]) %}
        {% if s1t in ['unavailable', 'unknown'] %}{% set ns.items = ns.items + ['Chamber S1 temp'] %}{% endif %}
        {% if s1h in ['unavailable', 'unknown'] %}{% set ns.items = ns.items + ['Chamber S1 hum'] %}{% endif %}
        {% if s2t in ['unavailable', 'unknown'] %}{% set ns.items = ns.items + ['Chamber S2 temp'] %}{% endif %}
        {% if s2h in ['unavailable', 'unknown'] %}{% set ns.items = ns.items + ['Chamber S2 hum'] %}{% endif %}
        {{ ns.items | join(', ') }}
      any_offline: >
        {{ s1t in ['unavailable', 'unknown']
           or s1h in ['unavailable', 'unknown']
           or s2t in ['unavailable', 'unknown']
           or s2h in ['unavailable', 'unknown'] }}
  - choose:
    - conditions:
      - condition: template
        value_template: "{{ any_offline }}"
      sequence:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.ventilation_pulse_mode
      - service: switch.turn_off
        target:
          entity_id:
          - switch.fogger_switch
          - switch.vifter_switch
      - service: timer.cancel
        target:
          entity_id: timer.ventilation_cycle
      - service: notify.mobile_app_pixel_9a
        data:
          title: "\U0001F6AB VPD System blokkert ved oppstart"
          message: >
            Sensorer offline etter omstart: {{ offline_list }}.
            VPD-systemet er IKKE startet. Sjekk ZHA og sensorene.
          data:
            priority: high
            channel: VPD_Alerts
  mode: single
- id: vpd_system_disable_automations
  alias: 'VPD System: Hardware Off When Stopped'
  description: Slår av hardware (fogger, vifte, lys) og sender notifikasjon når systemet deaktiveres. Timer kanselleres av ventilation_pulse_stop_v2.
  trigger:
  - platform: state
    entity_id: input_boolean.ventilation_pulse_mode
    from: 'on'
    to: 'off'
  action:
  - service: switch.turn_off
    target:
      entity_id:
      - switch.fogger_switch
      - switch.vifter_switch
  - service: light.turn_off
    target:
      entity_id: light.fruktenkammer
  - service: notify.mobile_app_pixel_9a
    data:
      title: 'VPD System Stopped'
      message: 'VPD Control System deaktivert. Fogger og vifte slått av.'
      data:
        priority: normal
        channel: VPD_System
  mode: single
- id: chamber_light_on_morning
  alias: 'Chamber Light: Auto ON 06:00'
  description: Slår på lyset i kammeret automatisk kl 06:00
  triggers:
  - trigger: time
    at: '06:00:00'
  conditions: []
  actions:
  - service: light.turn_on
    target:
      entity_id: light.fruktenkammer
  mode: single
- id: ach_sync_pinning
  alias: 'ACH: Sync Pinning Cycle Timer'
  description: >
    Ny ACH-definisjon: 1 ACH = 120s på-tid (én komplett luftutskifting).
    Når ACH endres: restart timer med ny off-tid = (3600/ACH) - on_duration.
    ON-tid er fast 120s og endres ikke.
  triggers:
  - trigger: state
    entity_id: input_number.ach_target_pinning
  conditions:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: state
    entity_id: input_boolean.pinning_phase
    state: 'on'
  actions:
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: >
        {% set ach = trigger.to_state.state | float(6) %}
        {% set on_sec = states('input_number.ventilation_on_duration_pinning') | int(120) %}
        {% set off_sec = ((3600 / ach) - on_sec) | int %}
        {{ [off_sec, 30] | max }}
  mode: single

- id: ach_sync_fruiting
  alias: 'ACH: Sync Fruiting Cycle Timer'
  description: >
    Ny ACH-definisjon: 1 ACH = 120s på-tid (én komplett luftutskifting).
    Når ACH endres: restart timer med ny off-tid = (3600/ACH) - on_duration.
    ON-tid er fast 120s og endres ikke.
  triggers:
  - trigger: state
    entity_id: input_number.ach_target_fruiting
  conditions:
  - condition: state
    entity_id: input_boolean.ventilation_pulse_mode
    state: 'on'
  - condition: state
    entity_id: input_boolean.pinning_phase
    state: 'off'
  actions:
  - service: timer.start
    target:
      entity_id: timer.ventilation_cycle
    data:
      duration: >
        {% set ach = trigger.to_state.state | float(7) %}
        {% set on_sec = states('input_number.ventilation_on_duration_fruiting') | int(120) %}
        {% set off_sec = ((3600 / ach) - on_sec) | int %}
        {{ [off_sec, 30] | max }}
  mode: single

- id: chamber_light_off_evening
  alias: 'Chamber Light: Auto OFF 18:00'
  description: Slår av lyset i kammeret automatisk kl 18:00
  triggers:
  - trigger: time
    at: '18:00:00'
  conditions: []
  actions:
  - service: light.turn_off
    target:
      entity_id: light.fruktenkammer
  mode: single

```

---

# input_numbers_vpd.yaml
> Konfigurerbare parametere (VPD-mål, ACH, etc.)

```yaml
# VPD Control System - Input Numbers
# Ventilasjons-pulsstyring
# ACH-definisjon: 1 ACH = 120s på-tid = én komplett luftutskifting (empirisk målt)
# ACH-target styrer frekvens (n ganger/time). Off-tid = (3600/ACH) - on_duration (beregnes av timer)
ventilation_on_duration_pinning:
  name: Ventilation ON Duration (Pinning)
  min: 60
  max: 150
  step: 5
  unit_of_measurement: "s"
  icon: mdi:fan-clock
  initial: 120

ventilation_on_duration_fruiting:
  name: Ventilation ON Duration (Fruiting)
  min: 60
  max: 150
  step: 5
  unit_of_measurement: "s"
  icon: mdi:fan-clock
  initial: 120

# VPD-styring (DYNAMISK) - Optimalisert for 15°C/17°C
target_vpd_pinning:
  name: Target VPD Pinning Phase
  min: 0.05
  max: 0.30
  step: 0.01
  unit_of_measurement: "kPa"
  icon: mdi:sprout
  initial: 0.10

target_vpd_fruiting:
  name: Target VPD Fruiting Phase
  min: 0.05
  max: 0.35
  step: 0.01
  unit_of_measurement: "kPa"
  icon: mdi:mushroom
  initial: 0.12

# ACH-styring (luftutskiftninger per time)
ach_target_pinning:
  name: ACH Target (Pinning)
  min: 2
  max: 15
  step: 1
  unit_of_measurement: "h⁻¹"
  icon: mdi:fan-speed-1
  initial: 6.0

ach_target_fruiting:
  name: ACH Target (Fruiting)
  min: 2
  max: 15
  step: 1
  unit_of_measurement: "h⁻¹"
  icon: mdi:fan-speed-3
  initial: 7.0

# Hysterese
vpd_hysteresis:
  name: VPD Hysteresis
  min: 0.01
  max: 0.10
  step: 0.01
  unit_of_measurement: "kPa"
  icon: mdi:delta
  initial: 0.02

```

---

# input_booleans_vpd.yaml
> Systemtilstander (pulse_mode, pinning_phase)

```yaml
# VPD Control System - Input Booleans

# Aktivere/deaktivere pulsmodus
ventilation_pulse_mode:
  name: Ventilation Pulse Mode
  icon: mdi:fan-auto
  initial: false

# Pinning vs Fruiting fase
pinning_phase:
  name: Pinning Phase
  icon: mdi:sprout
  initial: false

```

---

# timer_vpd.yaml
> Ventilasjonssyklus-timer

```yaml
# VPD Control System - Timer
ventilation_cycle:
  name: Ventilation Cycle Timer
  icon: mdi:timer-outline

pinning_phase_countdown:
  name: Pinning Phase Auto-Return
  duration: "48:00:00"
  icon: mdi:timer-sand
  restore: true

```

---
