#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dbus_emsesp'))
from dummy import DummyEmsEspClient
from model import EmsEspModelMapper
config=json.loads((ROOT/'config/config.json').read_text())
raw,_=DummyEmsEspClient(config['dummy']).read_all()
state=EmsEspModelMapper(config['emsesp_mapping'],9000).map(raw,'dummy-test')
assert state.outside_temperature_c is not None
assert state.electrical_energy_total_kwh is not None
assert state.mode in ('standby','heating','dhw','defrost','cooling')
print(json.dumps(state.as_dict(),indent=2,ensure_ascii=False))
print('OK')
