import json
import ssl
import urllib.error
import urllib.request


class EmsEspError(RuntimeError):
    pass


class EmsEspClient:
    def __init__(self, config):
        self.base_url = config["base_url"].rstrip("/")
        self.token = config.get("access_token", "").strip()
        self.timeout = float(config.get("timeout_seconds", 5))
        self.verify_tls = bool(config.get("verify_tls", True))
        self.endpoints = config.get("endpoints", {})

    def _get_json(self, path):
        request = urllib.request.Request(
            self.base_url + path,
            headers={"Accept": "application/json", "User-Agent": "venus-os-dbus-emsesp/0.4.0"},
        )
        if self.token:
            request.add_header("Authorization", "Bearer " + self.token)
        context = None
        if self.base_url.startswith("https://") and not self.verify_tls:
            context = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=context) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
            raise EmsEspError("GET {} failed: {}".format(path, exc)) from exc

    def read_all(self):
        data, errors = {}, {}
        for name, path in self.endpoints.items():
            try:
                data[name] = self._get_json(path)
            except EmsEspError as exc:
                errors[name] = str(exc)
        if not data:
            raise EmsEspError("all EMS-ESP endpoints failed: {}".format(errors))
        return data, errors
