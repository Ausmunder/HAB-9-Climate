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
