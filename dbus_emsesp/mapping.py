_MISSING = object()


def lookup(data, dotted_path):
    current = data
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def normalize(value):
    if isinstance(value, dict) and "value" in value:
        value = value["value"]
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        low = text.lower()
        if low in ("true", "on", "yes", "active"):
            return 1
        if low in ("false", "off", "no", "inactive"):
            return 0
        try:
            return float(text.replace(",", "."))
        except ValueError:
            return text
    return value


def first_value(data, candidates, default=None):
    for candidate in candidates:
        value = lookup(data, candidate)
        if value is not _MISSING and value is not None and value != "":
            return normalize(value)
    return default
