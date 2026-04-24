#!/usr/bin/env python3
"""Convert VPD dashboard from YAML to JSON for Home Assistant deployment."""

import json
import yaml

# Read YAML dashboard
with open('vpd_dashboard_split_screen_pro.yaml', 'r', encoding='utf-8') as f:
    dashboard_config = yaml.safe_load(f)

# Wrap in HA storage format
storage_format = {
    "version": 1,
    "minor_version": 1,
    "key": "lovelace.mushroom_chamber",
    "data": {
        "config": dashboard_config
    }
}

# Write JSON dashboard
with open('dashboard.json', 'w', encoding='utf-8') as f:
    json.dump(storage_format, f, indent=2, ensure_ascii=False)

print("Dashboard converted: dashboard.json")
print("Deploy with: ssh ha \"cat > /config/.storage/lovelace.mushroom_chamber\" < dashboard.json")
