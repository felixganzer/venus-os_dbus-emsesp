#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dbus_emsesp"))
from distributor import PowerDistributor
from dummy import DummyEmsEspClient

config = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
client = DummyEmsEspClient(config.get("dummy", {}))
distributor = PowerDistributor()
data, _ = client.read_all()
hp = data["heatpump"]
result = distributor.distribute(hp["power"], hp["status"], hp["auxheaterpower"], hp["auxheateractive"])
assert abs(result["heating"] + result["dhw"] + result["aux_heater"] - result["total"]) < 0.001
print(json.dumps(result, indent=2, ensure_ascii=False))
print("OK: Summe der drei Geraete entspricht der Gesamtleistung.")
