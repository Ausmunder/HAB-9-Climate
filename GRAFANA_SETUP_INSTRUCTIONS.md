# Grafana VPD Dashboard Setup

## 📋 Forutsetninger

✅ Grafana er installert på `http://192.168.1.251:3000`
✅ Home Assistant integrasjon er konfigurert i Grafana

---

## 🚀 Installasjon

### Steg 1: Installer Home Assistant Data Source (hvis ikke allerede gjort)

1. Åpne Grafana: `http://192.168.1.251:3000`
2. Gå til **Configuration** → **Data Sources**
3. Klikk **Add data source**
4. Søk etter **Home Assistant**
5. Konfigurer:
   - **URL**: `http://192.168.1.251:8123`
   - **Access**: Server (default)
   - **Auth**: Forward OAuth Identity (hvis aktuelt)
   - **Long-Lived Access Token**:
     - Gå til Home Assistant → Profil → **Long-Lived Access Tokens** → Create Token
     - Kopier token til Grafana
6. Klikk **Save & Test**

---

### Steg 2: Importer VPD Dashboard

#### Metode A: API (anbefalt)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GRAFANA_API_KEY" \
  -d @K:/grafana_vpd_dashboard.json \
  http://192.168.1.251:3000/api/dashboards/db
```

#### Metode B: Web UI

1. Åpne Grafana: `http://192.168.1.251:3000`
2. Klikk **Dashboards** (venstre meny) → **Import**
3. Klikk **Upload JSON file**
4. Velg `K:\grafana_vpd_dashboard.json`
5. Velg **Home Assistant** som data source
6. Klikk **Import**

---

### Steg 3: Verifiser Dashboard URL

Dashboardet skal være tilgjengelig på:
```
http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring
```

**Kiosk URL (brukt i Home Assistant iframe):**
```
http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring?orgId=1&refresh=30s&theme=dark&kiosk=tv
```

---

### Steg 4: Oppdater Home Assistant Dashboard

Dashboard er **allerede oppdatert** i `K:\vpd_dashboard_split_screen_pro.yaml`:

```yaml
# GRAFANA VPD MONITORING DASHBOARD
- type: iframe
  url: 'http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring?orgId=1&refresh=30s&theme=dark&kiosk=tv'
  aspect_ratio: 100%
  title: VPD Climate Monitoring
```

Last inn dashboardet i Home Assistant:
1. Gå til dashboard → **Edit Dashboard**
2. Klikk **⋮** → **Raw configuration editor**
3. Kopier hele innholdet fra `K:\vpd_dashboard_split_screen_pro.yaml`
4. Lim inn og klikk **Save**

---

## 📊 Dashboard Innhold

### Grafer (12h historikk):
1. **Temperature & Humidity** - Dual-axis line graph
2. **VPD** - Line graph med threshold annotations (0.15 kPa pinning, 0.20 kPa fruiting)
3. **Climate Health Score** - Area chart med fargekoding (rød/orange/grønn)
4. **VPD Stability Score** - Area chart

### Stat Panels (live verdier):
5. **Current VPD** - Color-coded stat panel
6. **Current Temperature** - Color-coded stat panel
7. **Current Humidity** - Color-coded stat panel
8. **Climate Health** - Color-coded stat panel

---

## 🎨 Farger og Thresholds

### VPD:
- 🟢 **Grønn**: < 0.23 kPa (optimal)
- 🟡 **Gul**: 0.23-0.30 kPa (akseptabel)
- 🟠 **Orange**: 0.30-0.35 kPa (høy)
- 🔴 **Rød**: > 0.35 kPa (kritisk)

### Climate Health:
- 🟢 **Grønn**: ≥ 70% (utmerket)
- 🟠 **Orange**: 40-69% (akseptabel)
- 🔴 **Rød**: < 40% (kritisk)

### Temperature:
- 🔵 **Blå**: < 17°C (for kaldt)
- 🟢 **Grønn**: 17-19°C (optimal)
- 🟡 **Gul**: > 19°C (for varmt)

### Humidity:
- 🔴 **Rød**: < 85% (for lavt)
- 🟡 **Gul**: 85-90% (litt lavt)
- 🟢 **Grønn**: 90-95% (optimalt)
- 🟠 **Orange**: > 95% (for høyt)

---

## 🔧 Feilsøking

### Problem: "Panel plugin not found"
**Løsning**: Installer manglende plugins via Grafana CLI:
```bash
grafana-cli plugins install <plugin-name>
systemctl restart grafana-server
```

### Problem: "Data source not found"
**Løsning**: Verifiser at Home Assistant data source er konfigurert riktig i Grafana.

### Problem: "No data" i grafene
**Løsning**:
1. Sjekk at entity_ids eksisterer i Home Assistant
2. Verifiser at Long-Lived Access Token er gyldig
3. Sjekk Grafana logs: `journalctl -u grafana-server -f`

### Problem: iframe viser "Refused to connect"
**Løsning**:
1. Sjekk at Grafana er tilgjengelig på `http://192.168.1.251:3000`
2. Verifiser at Home Assistant har tilgang til Grafana (samme nettverk)
3. Sjekk Grafana `allow_embedding` setting i `/etc/grafana/grafana.ini`:
   ```ini
   [security]
   allow_embedding = true
   ```

---

## ✅ Ferdig!

Dashboard er nå klar til bruk! 🎉

**Dashboard URL**: http://192.168.1.251:3000/d/vpd-monitoring/vpd-climate-monitoring

**Home Assistant Dashboard**: Oppdater dashboard via Raw Configuration Editor med innholdet fra `vpd_dashboard_split_screen_pro.yaml`.
