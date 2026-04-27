# HAB-9 VPD Control System v2.0 - Complete Documentation

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

HAB-9 VPD Control System er et klimakontrollsystem for soppdyrkingskammere. Systemet bruker **VPD-first med safety overrides** som arkitekturprinsipp.

### Kontrollhierarki

```
Prioritet 1 — Safety   →  overstyrer alt (RH > 98%, power-feil, lockout)
Prioritet 2 — VPD      →  primær kontroll, event-drevet
Prioritet 3 — ACH      →  ventilasjon, uavhengig syklus
```

### Key Metrics

| Phase | Temperature | Target VPD | ACH | Fan on-tid |
|-------|-------------|------------|-----|------------|
| **Pinning** | 15°C | 0.10 kPa | 6 | 120s (konfigurerbar) |
| **Fruiting** | 17°C | 0.12 kPa | 7 | 120s (konfigurerbar) |

> **Pause per halvburst:** `(3600/ACH − fan_total_on_time) / 2` sekunder.
> Eksempel fruiting: `(3600/7 − 120) / 2 ≈ 197s` pause mellom burstene.

---

## ✨ Features

### Core Features

✅ **VPD-first kontroll (event-drevet)**
- Fogger trigges på VPD state change — ingen polling, kortere reaksjonstid
- Hysteresis-band (default ±0.01 kPa) forhindrer oscillasjon
- Adaptiv retrigger: re-evaluer umiddelbart etter burst hvis VPD > target + 0.05 kPa

✅ **Dual-Phase Control**
- Pinning Phase (15°C, 0.10 kPa VPD, ACH 6)
- Fruiting Phase (17°C, 0.12 kPa VPD, ACH 7)
- One-click phase toggle, 48-timers auto-retur til fruiting

✅ **Anti-oscillasjon**
- Fogger blokkert 30s etter viftestart (`input_boolean.fogger_blocked_by_fan`)
- Forhindrer at vifteindusert VPD-spike trigger unødvendig fogging

✅ **Safety overrides (Prioritet 1)**
- RH hard cutoff: fogger OFF umiddelbart ved RH > 98% (ingen conditions)
- Power-feil: fogger/vifte OFF ved underpower eller overpower
- Fogger lockout: aktiveres ved power-feil, resetter etter konfigurerbar tid
- Fogger watchdog: 3 min maks (ned fra 10 min)

✅ **Power verification**
- `sensor.vifter_power` og `sensor.fogger_power` verifisert etter oppstart
- Underpower → OFF. Fogger: lockout aktiveres
- Overpower → OFF + varsling
- Alle grenser konfigurerbare via input_number

✅ **Forenklet ventilasjon**
- ÉN automation + ÉN timer (erstatter 4 timer-automasjoner)
- `fan_total_on_time` konfigurerbar (default 120s)
- Sekvens: burst 1 → pause → burst 2 → restart timer

✅ **Trygg oppstart**
- Hardware OFF → 180s → system ON
- Nullstiller `fogger_lockout` og `fogger_blocked_by_fan` ved boot

✅ **Monitoring & varsling**
- VPD kritisk høy (>0.35 kPa i 15 min)
- Fogger inaktiv 30 min ved høy VPD
- Vifte inaktiv lenger enn forventet ACH-intervall
- Anomali-deteksjon: rask temp/fuktighetsendring, sensor offline, temp/RH utenfor område
- Daglig morgenrapport kl 08:00

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

```
/config/
├── automations.yaml                  # Hjem-automasjoner, varsler, systemlivssyklus
├── fogger.yaml                       # All fogger-logikk (VPD-trigger, safety, watchdog)
├── ventilation.yaml                  # Ventilasjonssyklus (sekvens-automation)
├── power_safety.yaml                 # Power-verifisering for vifte og fogger
├── configuration_vpd_sensors.yaml    # Template-sensorer, statistikk, integrasjoner
├── input_numbers_vpd.yaml            # VPD-parametere og power-grenser
├── input_booleans_vpd.yaml           # System-toggles, lockout, anti-oscillasjon
├── timer_vpd.yaml                    # Timere
├── scripts_vpd.yaml                  # Hjelpeskripter
└── hab9_climate_dashboard.yaml       # Lovelace dashboard
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

**Sensorer (hardware):**
- `sensor.chamber_sensor_1_temperature` / `sensor.chamber_sensor_1_humidity` — Aqara T1 (primær)
- `sensor.chamber_sensor_2_temperature` / `sensor.chamber_sensor_2_humidity` — Aqara T1 (primær)
- `sensor.kammeret_temperature` / `sensor.kammeret_humidity` — Fallback
- `sensor.vifter_power` — Effektmåling vifte
- `sensor.fogger_power` — Effektmåling fogger

**Beregnede sensorer:**
- `sensor.chamber_avg_temp` — Gjennomsnitt av T1-sensorer (med bounds-sjekk)
- `sensor.chamber_avg_humidity` — Gjennomsnitt av T1-sensorer (+3% kalibrering)
- `sensor.chamber_current_vpd` — VPD beregnet fra Magnus-formel
- `sensor.incubation_avg_temp` / `sensor.incubation_avg_humidity` — Inkubasjon (kun monitoring)

**Kontroll (input_boolean):**
- `input_boolean.system_enabled` — Master ON/OFF
- `input_boolean.pinning_phase` — Pinning/Fruiting fase-toggle
- `input_boolean.fogger_lockout` — Safety lockout (aktiveres ved power-feil)
- `input_boolean.fogger_blocked_by_fan` — Anti-oscillasjon (30s blokkering)

**Kontroll (input_number):**
- `input_number.target_vpd_pinning` / `target_vpd_fruiting` — VPD-mål per fase
- `input_number.vpd_hysteresis` — Hysteresebånd (kPa)
- `input_number.ach_target_pinning` / `ach_target_fruiting` — ACH per fase
- `input_number.fogger_burst_duration` — Burst-varighet (default 14s)
- `input_number.fan_total_on_time` — Total ON-tid per syklus (default 120s)
- `input_number.fan_power_min` / `fan_power_max` — Power-grenser vifte
- `input_number.fogger_power_min` / `fogger_power_max` — Power-grenser fogger
- `input_number.power_check_delay` — Forsinkelse før power-sjekk
- `input_number.fogger_lockout_time` — Lockout-varighet ved feil

**Timere:**
- `timer.ventilation_cycle` — Aktiv nedtelling til neste ventilasjonssyklus
- `timer.fogger_burst` — Begrenser fogger-burst til `fogger_burst_duration`
- `timer.fogger_lockout_timer` — Teller ned lockout-perioden

**Switches:**
- `switch.fogger_switch` — Fogger (ZHA Zigbee)
- `switch.vifter_switch` — Vifte (ZHA Zigbee)
- `light.fruktenkammer` — Vekstlys

**Automasjoner (fordelt på filer):**

*fogger.yaml:*
- `fogger_vpd_control` — Primær VPD-trigger (event-drevet)
- `fogger_burst_end` — Auto-off etter burst
- `fogger_blocked_by_fan_trigger` — Anti-oscillasjon 30s
- `fogger_adaptive_retrigger` — Rask retrigger ved kritisk VPD
- `fogger_watchdog_safety` — 3 min watchdog
- `fogger_rh_hard_cutoff` — RH > 98% → OFF umiddelbart

*ventilation.yaml:*
- `ventilation_cycle_sequence` — Én sekvens-automation (erstatter 4)
- `ach_sync` — Restart syklus ved ACH-endring
- `ventilation_timer_idle_watchdog` — 10 min idle recovery
- `fan_watchdog_safety` — 90s maks fan-kjøretid

*power_safety.yaml:*
- `fan_power_failure` — Vifte underpower → OFF + restart syklus
- `fan_overpower` — Vifte overpower → OFF
- `fogger_power_failure` — Fogger underpower → lockout
- `fogger_overpower` — Fogger overpower → OFF
- `fogger_lockout_reset` — Reset lockout etter timer

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
