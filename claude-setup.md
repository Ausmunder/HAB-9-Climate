# VPD-home Setup for Claude Code

## Repository
- **Git repo**: https://github.com/Ausmunder/VPD-home.git
- **Branch**: main

## GitHub Account
- **Username**: Ausmunder
- **Email**: assmund@gmail.com
- **Full Name**: Aasmund A.
- **Password**: cB4C#544KadAbtR! ← GitHub-kontopassord (IKKE gyldig for git-operasjoner)
- **GitHub PAT**: Satt opp 2026-02-24, lagret i Windows Credential Manager via GCM.
  Scope: `repo`. Utløper etter valgt periode — fornye på https://github.com/settings/tokens

## Directory Structure

### Development Environment (d:\dev\VPD-home\)
```
d:\dev\VPD-home\                  ← Git working directory (primary workspace)
├── automations_vpd_v3.yaml       ← Home Assistant automations (10 automations)
├── configuration_vpd_sensors.yaml ← Template sensors for VPD calculations
├── input_numbers_vpd.yaml        ← VPD system parameters
├── input_booleans_vpd.yaml       ← VPD system toggles
├── scripts_vpd.yaml              ← Helper scripts
├── vpd_dashboard_split_screen_pro.yaml ← Lovelace dashboard
├── grafana_vpd_dashboard.json    ← Grafana dashboard configuration
├── README.md                     ← System documentation
├── SYSTEM_ARCHITECTURE.md        ← Technical architecture
├── INSTALLATION_CHECKLIST.md     ← Installation guide
├── CHANGELOG.md                  ← Version history
├── GRAFANA_SETUP_INSTRUCTIONS.md ← Grafana setup
├── FILE_MANIFEST.md              ← Package contents
└── claude-setup.md               ← This file
```

**CRITICAL: Home Assistant Integration**
- Files are deployed DIRECTLY to `/config/` on HA (NOT a VPD-home subdirectory)
- File mapping:
  ```
  automations_vpd_v3.yaml  → /config/automations.yaml
  configuration_vpd_sensors.yaml → /config/configuration.yaml
  input_numbers_vpd.yaml → /config/input_numbers_vpd.yaml
  input_booleans_vpd.yaml → /config/input_booleans_vpd.yaml
  scripts_vpd.yaml → /config/scripts.yaml
  timer_vpd.yaml → /config/timer_vpd.yaml
  ```
- `configuration.yaml` uses `!include` to reference the other YAML files
- Dashboard is stored as JSON in `/config/.storage/lovelace.mushroom_chamber`
- Deploy via SSH: `ssh ha "cat > /config/automations.yaml" < automations_vpd_v3.yaml`
- After deployment: `ssh ha "ha core restart"`

## Project Details

### System Purpose
VPD (Vapor Pressure Deficit) Control System for automated mushroom cultivation climate control. Manages temperature, humidity, and fog output through intelligent Home Assistant automations.

### Current Version
**Version 3.7.2** (Released: 2026-04-20)
- **Sensor-sjekk ved oppstart:** ny automation blokkerer VPD-systemet og varsler mobil hvis Aqara-sensorene ikke er online 85s etter boot
- **Kritisk bugfix — fogger-loop:** unavailable VPD ga fallback 9.99 kPa → fogger fyrte hvert minutt. Nå: unavailable VPD = False (fail-safe off)
- **Chamber sensors:** Sonoff SNZB-02WD byttet til 2x Aqara Temperature and Humidity Sensor T1
- **Fikset chamber_avg_humidity:** bruker nå dual Aqara T1-sensorer (ikke Netatmo kammeret_humidity)
- **Fikset sensor_health_status:** fjernet legacy kammeret_humidity-referanse
- **safety_fan_off_on_ha_start:** delay økt 60s → 90s, slår nå også av fogger ved boot

**Version 3.7.0** (Released: 2026-04-09)
- **Ny ACH-definisjon:** 1 ACH = 120s fan on-tid. ACH n = viften kjører n ganger per time
- **Timer-basert ventilasjon:** `timer.ventilation_cycle` erstatter `time_pattern`-trigger
  - OFF-tid beregnes: `(3600/ACH) − 120s` (min 30s)
  - ACH justeres via UI — timer restarter automatisk med ny frekvens
- **Fan Watchdog:** økt til 150s (var 120s = lik on-tid → utløste hver syklus)
- **Fjernet startup-konflikter:** 3 automater → 1 (`safety_fan_off_on_ha_start`)
- **Fjernet enable/disable-mekanisme:** erstattet av `ventilation_pulse_mode`-conditions
- **Fogger koblet til input_numbers:** UI-endringer av VPD-mål virker nå
- **ACH-aware fan-alert:** dynamisk forventet off-tid basert på ACH
- **Sensor-rename:** incubation sensor 1 ZHA-enhetsnavn endret → entity IDs nå `sensor.incubation_sensor_1_*`
- **Dashboard:** data.config.views-struktur (ikke data.views), ventilasjonsstatus-seksjon lagt til
- Fogger burst: 14s, VPD-hysteresis: 0.02 kPa
- Fog After Ventilation: 14s proaktiv burst etter fan OFF

### Growth Phases

**Pinning Phase:**
- Target Temperature: **15°C**
- Target Humidity: ~94% RH (dynamic, calculated from VPD)
- Target VPD: **0.10 kPa**
- Ventilation: 120s ON / ~480s OFF (sykluslengde ~600s, 10 min)
- Air Changes per Hour (ACH): **6** (1 ACH = 120s on-tid)

**Fruiting Phase:**
- Target Temperature: **17°C**
- Target Humidity: ~93% RH (dynamic, calculated from VPD)
- Target VPD: **0.12 kPa**
- Ventilation: 120s ON / ~394s OFF (sykluslengde ~514s, 8.6 min)
- Air Changes per Hour (ACH): **7** (1 ACH = 120s on-tid)

### Hardware Integration
- Chamber sensors: 2x Aqara Temperature and Humidity Sensor T1 (ZHA) - `sensor.chamber_sensor_1_*`, `sensor.chamber_sensor_2_*`
- Incubation sensors: 2x Sonoff SNZB-02P (ZHA) - `sensor.incubation_sensor_1_*`, `sensor.incubation_sensor_2_*`
  - (Sensor 1 ble omdøpt i ZHA fra "Sensor Incubation Sensor 1" → "Incubation Sensor 1" 2026-04-09)
- VPD: Calculated template sensor (`sensor.chamber_current_vpd`) fra chamber_avg_temp og chamber_avg_humidity
- Fogger/humidifier: `switch.fogger_switch` (ZHA Zigbee)
- Ventilation fan: `switch.vifter_switch` (ZHA Zigbee)
- Ventilation timer: `timer.ventilation_cycle`
- Chamber light: `light.fruktenkammer`

### Key Features
- Dual-phase control (Pinning/Fruiting)
- Real-time VPD calculation using Magnus formula
- Dynamic RH setpoint generation
- Timer-basert ventilasjon (`timer.ventilation_cycle`) — ACH-justerbar via UI
- Emergency stop at 98% RH (condensation) or VPD normalisert
- Mobile notifications for critical events
- ACH-aware inaktivitetsalert for fan

## Working Method

### Preferred Workflow
1. **Read/Edit**: Work directly with files in `d:\dev\VPD-home\` (Git workspace)
2. **Test locally**: Validate YAML syntax and configuration
3. **Deploy**: Deploy via SSH: `ssh ha "cat > /config/automations.yaml" < automations_vpd_v3.yaml`
4. **Restart HA**: `ssh ha "ha core restart"`

### File Access
- Git repo (`d:\dev\VPD-home\`) is source of truth
- Deploy to HA via SSH (see deployment section above)
- Dashboard deploys as JSON to `.storage/lovelace.mushroom_chamber`

## Deployment Process

### Deploy Configuration to Home Assistant

**Deploy via SSH:**
```bash
# From d:\dev\VPD-home\
ssh ha "cat > /config/automations.yaml" < automations_vpd_v3.yaml
ssh ha "cat > /config/configuration.yaml" < configuration_vpd_sensors.yaml
ssh ha "cat > /config/input_numbers_vpd.yaml" < input_numbers_vpd.yaml
ssh ha "cat > /config/scripts.yaml" < scripts_vpd.yaml
```

**Dashboard (YAML → JSON):**
Dashboard must be converted to JSON and written to `.storage/lovelace.mushroom_chamber`.
Use Python with PyYAML to convert, then deploy via SSH.

**After Deployment:**
```bash
ssh ha "ha core restart"
```

### Verify Configuration
```bash
# Check Home Assistant logs for errors
ssh ha "ha core logs 2>&1 | grep -i 'error\|missing' | grep -v chromecast | grep -v music"
```

## SSH Access to Home Assistant

### Setup SSH Connection
Run this PowerShell script to configure SSH access:

```powershell
# Home Assistant SSH Setup
$sshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
}

$privateKey = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDXH9eluC0DpHXjvUwgJ7KaT0BBpWtTckU4kbgSiYsg5wAAAKAZypZ7GcqW
ewAAAAtzc2gtZWQyNTUxOQAAACDXH9eluC0DpHXjvUwgJ7KaT0BBpWtTckU4kbgSiYsg5w
AAAEDDRdiX4j9Sei4l9PPYaRyOC6b8WHpzg/Na8B472kk4NNcf16W4LQOkdeO9TCAnsppP
QEGla1NyRTiRuBKJiyDnAAAAGWNsYXVkZS1jb2RlQGhvbWVhc3Npc3RhbnQBAgME
-----END OPENSSH PRIVATE KEY-----
"@

$keyPath = "$sshDir\ha_ed25519"
$privateKey | Out-File -FilePath $keyPath -Encoding ASCII -NoNewline

icacls $keyPath /inheritance:r | Out-Null
icacls $keyPath /grant:r "$($env:USERNAME):(R)" | Out-Null

$configPath = "$sshDir\config"
$configContent = @"
Host ha
    HostName 192.168.1.251
    User hassio
    IdentityFile ~/.ssh/ha_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
"@

if (Test-Path $configPath) {
    "`n$configContent" | Out-File -FilePath $configPath -Encoding ASCII -Append
} else {
    $configContent | Out-File -FilePath $configPath -Encoding ASCII
}

Write-Host "SSH setup complete. Test with: ssh ha"
```

### Connect to Home Assistant
```bash
# Simple connection (preferred)
ssh ha

# Or full connection string
ssh hassio@192.168.1.251 -i ~/.ssh/ha_ed25519
```

**SSH Status**: ✅ Fully configured and working
- **User**: hassio (limited access)
- **Key Type**: ED25519
- **Fingerprint**: SHA256:D2owqzJwjiv0i3AVkUJzsxVVmhRrPAOzfqjDPxrJ4f4
- **Home Assistant IP**: 192.168.1.251
- **Home Assistant Version**: Core 2025.11.1, Supervisor 2026.01.1

### Home Assistant Paths
- **From HA SSH**: `/config/` (files deploy directly here, NOT a subdirectory)

### Common HA Commands

**Via SSH (hassio user):**
```bash
# HA system commands
ha core info
ha core logs
ha core restart
ha core stop
ha core start
```

**Via HA Terminal (root access):**
```bash
# Check Home Assistant configuration
ha core check

# View specific service logs
journalctl -u home-assistant@homeassistant.service -f
```

## Configuration Parameters

### Entity IDs (Actual HA entities)

**Chamber Sensors (2x Aqara Temperature and Humidity Sensor T1, ZHA):**
- `sensor.chamber_sensor_1_temperature` - Chamber sensor 1 temperature
- `sensor.chamber_sensor_1_humidity` - Chamber sensor 1 humidity
- `sensor.chamber_sensor_2_temperature` - Chamber sensor 2 temperature
- `sensor.chamber_sensor_2_humidity` - Chamber sensor 2 humidity

**Incubation Room Sensors (2x Sonoff SNZB-02P, ZHA):**
- `sensor.incubation_sensor_1_temperature` - Incubation sensor 1 temperature
- `sensor.incubation_sensor_1_humidity` - Incubation sensor 1 humidity
- `sensor.incubation_sensor_2_temperature` - Incubation sensor 2 temperature
- `sensor.incubation_sensor_2_humidity` - Incubation sensor 2 humidity

**Calculated VPD:**
- `sensor.chamber_current_vpd` - VPD (calculated from chamber_avg_temp and chamber_avg_humidity)

**Template Sensors (calculated):**
- `sensor.chamber_avg_temp` - Averaged temperature
- `sensor.chamber_avg_humidity` - Averaged humidity
- `sensor.dynamic_rh_setpoint` - Dynamic RH target based on VPD
- `sensor.climate_health_score` - Combined health score (0-100%)
- `sensor.vpd_stability_score` - VPD stability (0-100%)
- `sensor.sensor_health_status` - Sensor health (Healthy/Degraded/Critical)

**Switches (ZHA - Zigbee):**
- `switch.fogger_switch` - Fogger/humidifier (ZHA, unique_id: a4:c1:38:14:82:cb:9b:75-1)
- `switch.vifter_switch` - Ventilation fan (ZHA, unique_id: a4:c1:38:68:4e:38:0f:e8-1)

**Automation Entity IDs (generated from alias field):**
- `automation.vpd_control_fogger_burst_v3` - Fogger 14s bursts (fail-safe: stopper ved unavailable VPD)
- `automation.vpd_control__emergency_stop_v3` - Emergency stop
- `automation.ventilation_timer_v4` - Timer-basert ventilasjon
- `automation.vpd_control_fog_after_ventilation` - Proaktiv fog-burst etter fan OFF
- `automation.safety_fan_off_on_ha_start` - Fan+fogger AV ved boot, timer-start etter 90s
- `automation.startup_sensor_availability_check` - Blokkerer VPD-system hvis sensorer offline 85s etter boot

**Mobile Notifications:**
- `notify.mobile_app_pixel_9a` - Android push notifications

### Tunable Parameters (input_numbers_vpd.yaml)
All parameters can be adjusted via Home Assistant UI or YAML:
- VPD targets for pinning/fruiting phases
- Temperature and humidity setpoints
- Ventilation timing (ON/OFF durations)
- Fogger burst timing
- Hysteresis values

## Common Tasks

### Update Configuration
```bash
# After editing files in d:\dev\VPD-home\
# Deploy to Home Assistant via SSH
ssh ha "cat > /config/automations.yaml" < automations_vpd_v3.yaml
ssh ha "cat > /config/configuration.yaml" < configuration_vpd_sensors.yaml

# Restart HA to load changes
ssh ha "ha core restart"
```

### Monitor System
```bash
# View Home Assistant logs
ssh ha "ha core logs | grep -i vpd"

# Check automation status
ssh ha "ha automation list | grep vpd"

# View sensor values
ssh ha "ha sensor list | grep -i vpd"
```

### Troubleshooting
```bash
# Check configuration validity
ssh ha "ha core check"

# View recent errors
ssh ha "tail -100 /config/home-assistant.log | grep -i error"

# Restart specific automation
ssh ha "ha automation reload"
```

## Git Workflow

### Initial Setup
```bash
cd /d/dev/VPD-home
git init
git remote add origin https://github.com/Ausmunder/VPD-home.git
git pull origin main
```

### Commit Changes
```bash
cd /d/dev/VPD-home
git add .
git commit -m "Description of changes"
git push origin main
```

### Sync with Remote
```bash
cd /d/dev/VPD-home
git pull origin main
```

### GitHub Push Authentication (VIKTIG for Claude)

**Problem:** Git Credential Manager (GCM) åpner browser for auth — fungerer ikke i Claude sitt miljø (henger).
**GitHub krever PAT** (Personal Access Token) — ikke vanlig passord.

**Løsning A: Engangsoppsett via PAT (anbefalt)**
1. Gå til https://github.com/settings/tokens → Generate new token (classic)
2. Gi scope: `repo` → kopier tokenet
3. Lagre tokenet i credential store:
```bash
cd /d/dev/VPD-home
git credential approve << 'EOF'
protocol=https
host=github.com
username=Ausmunder
password=DIN_PAT_HER
EOF
```
4. Deretter fungerer `git push origin main` direkte fra Claude.

**Løsning B: Push manuelt én gang**
Åpne et vanlig terminalvindu → kjør `git push origin main` → GCM åpner browser → logg inn → token lagres automatisk.
Etter det fungerer `git push origin main` fra Claude også (GCM-token er lagret).

**Merk:** GitHub-passordet `cB4C#544KadAbtR!` er IKKE et PAT og godtas ikke for git-operasjoner.

**Status (2026-02-24):** PAT satt opp og lagret via `git credential approve`. `git push origin main` fungerer nå direkte fra Claude. Når token utløper: generer nytt PAT på GitHub og kjør Løsning A på nytt.

## Project Stack
- **Platform**: Home Assistant (Core 2025.11.1)
- **Configuration**: YAML-based
- **Automations**: Time-pattern triggers (immortal, cannot fail)
- **Dashboard**: Lovelace YAML
- **Monitoring**: Grafana (optional)
- **Notifications**: Home Assistant Companion App (Android)

## Safety Features
- **Startup sensor check:** blokkerer VPD-systemet og varsler mobil hvis Aqara-sensorer er offline 85s etter boot
- **Fail-safe fogger:** unavailable VPD → fogger fyrer IKKE (ikke lenger fallback 9.99 kPa)
- Emergency fogger stop when VPD normalizes (mid-burst cutoff)
- Maximum RH safety: fogger off at 95% RH
- Fogger Watchdog: auto-off after 30 seconds (hardware failsafe mot stuck-on)
- Fan Watchdog: auto-off after 150 seconds (hardware failsafe)
- Ventilation Safety Net: fan + fogger forced OFF on HA boot
- VPD System Disable: all hardware off when system toggled OFF
- VPD critical alert at 0.35 kPa for 15 min
- Fogger inactivity alert: notification if no activation for 30 min
- Fan inactivity alert: notification if no activation for 30 min
- Sensor anomaly detection (rapid changes, offline sensors)
- Mobile notifications for all critical events
- 48h auto-return from pinning to fruiting phase

## Documentation Files
- `README.md` - Complete system overview and usage guide
- `SYSTEM_ARCHITECTURE.md` - Technical internals and control logic
- `INSTALLATION_CHECKLIST.md` - Step-by-step installation guide
- `CHANGELOG.md` - Version history and migration guides
- `GRAFANA_SETUP_INSTRUCTIONS.md` - Optional Grafana integration
- `FILE_MANIFEST.md` - Package contents overview

## Last Verified
- Date: 2026-04-20
- Latest version: 3.7.2 (2026-04-20)
- Branch: main
- Home Assistant Version: Core 2026.4.1, OS 2026.4.1
- Pinning: 15°C, VPD 0.10 kPa, 120s ON / ~480s OFF, 6 ACH
- Fruiting: 17°C, VPD 0.12 kPa, 120s ON / ~394s OFF, 7 ACH
- VPD Hysteresis: 0.02 kPa
- Fog After Ventilation: 14s proaktiv burst etter fan OFF (VPD ≥ target)
- Chamber sensors: 2x Aqara Temperature and Humidity Sensor T1 (ZHA) — offset ukjent, sjekk etter paring
- Incubation sensors: 2x Sonoff SNZB-02P (ZHA)
- VPD: Calculated template sensor (`sensor.chamber_current_vpd`)
- Fogger: `switch.fogger_switch` (ZHA), burst 14s
- Fan: `switch.vifter_switch` (ZHA), watchdog 150s
- Ventilasjon: `timer.ventilation_cycle` (timer-basert, ikke time_pattern)

## Dashboard Deploy

Dashboard lagres som JSON i HA's `.storage/`:
```bash
# Konverter YAML → JSON med korrekt struktur
python3 -c "
import yaml, json
with open('vpd_dashboard_split_screen_pro.yaml', encoding='utf-8') as f:
    dc = yaml.safe_load(f)
storage = {'version': 1, 'minor_version': 1,
           'key': 'lovelace.mushroom_chamber',
           'data': {'config': dc}}  # KRITISK: data.config, ikke data direkte
with open('vpd_dashboard_split_screen_pro.json', 'w', encoding='utf-8') as f:
    json.dump(storage, f, ensure_ascii=False, indent=2)
"
ssh ha "cat > /config/.storage/lovelace.mushroom_chamber" < vpd_dashboard_split_screen_pro.json
ssh ha "ha core restart"
```

> **VIKTIG:** HA 2026.4.1 krever `data.config.views` — ikke `data.views` direkte.
