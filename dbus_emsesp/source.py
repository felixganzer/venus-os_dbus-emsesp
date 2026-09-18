import logging
import time

from emsesp import EmsEspError

LOG = logging.getLogger("dbus-emsesp.source")


class RestWithDummyFallback:
    def __init__(self, rest_client, dummy_client, model_mapper, config=None, clock=None):
        self.rest = rest_client
        self.dummy = dummy_client
        self.mapper = model_mapper
        self.config = config or {}
        self.clock = clock or time.time
        self.enabled = bool(self.config.get("enabled", True))
        self.after_failures = max(1, int(self.config.get("after_consecutive_failures", 1)))
        self.retry_seconds = max(1, int(self.config.get("rest_retry_seconds", 30)))
        self.failures = 0
        self.last_rest_attempt = 0.0
        self.using_fallback = False

    def read_state(self):
        now = self.clock()
        may_try_rest = not self.using_fallback or now - self.last_rest_attempt >= self.retry_seconds
        if may_try_rest:
            self.last_rest_attempt = now
            try:
                raw, errors = self.rest.read_all()
                self.failures = 0
                self.using_fallback = False
                return self.mapper.map(raw, source="rest"), errors
            except EmsEspError as exc:
                self.failures += 1
                LOG.warning("REST read failed (%d): %s", self.failures, exc)
                if not self.enabled or self.failures < self.after_failures:
                    raise
                self.using_fallback = True

        raw, errors = self.dummy.read_all()
        errors = dict(errors)
        errors["fallback"] = "dummy data active because REST is unavailable"
        return self.mapper.map(raw, source="dummy_fallback"), errors
