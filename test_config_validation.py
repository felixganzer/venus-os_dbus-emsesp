from dbus_emsesp.main import validate_config


def test_validate_config_requires_electrical_block():
    config = {
        "mode": "rest",
        "ems_esp": {
            "base_url": "http://example",
            "poll_interval_seconds": 10,
            "endpoints": {"boiler": "/api/boiler"},
        },
        "devices": {
            "heating": {"service_name": "svc", "device_instance": 1, "custom_name": "A", "product_name": "P", "product_id": 1},
            "dhw": {"service_name": "svc2", "device_instance": 2, "custom_name": "B", "product_name": "P2", "product_id": 2},
            "aux_heater": {"service_name": "svc3", "device_instance": 3, "custom_name": "C", "product_name": "P3", "product_id": 3},
        },
    }

    try:
        validate_config(config)
        assert False, "Expected a ValueError for missing electrical section"
    except ValueError:
        pass
