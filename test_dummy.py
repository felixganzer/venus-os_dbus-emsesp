#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "dbus_emsesp"))

from dummy import DummyEmsEspClient


def main():
    config = json.loads((PROJECT_DIR / "config" / "config.json").read_text())
    client = DummyEmsEspClient(config.get("dummy", {}))
    print("Dummy-Modus läuft. Abbruch mit Strg+C.")
    while True:
        data, errors = client.read_all()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        if errors:
            print("Fehler:", errors)
        time.sleep(5)


if __name__ == "__main__":
    main()
