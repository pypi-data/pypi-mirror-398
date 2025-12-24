import json, base64, datetime
from nacl.signing import VerifyKey
from kafkagraph.license.fingerprint import machine_fingerprint

PUBLIC_KEY_B64 = "REPLACE_WITH_YOUR_PUBLIC_KEY"

class SignedLicense:
    def __init__(self, path):
        self.path = path
        self.data = json.load(open(path))
        self.license = self.data["license"]
        self.signature = base64.b64decode(self.data["signature"])
        self.in_grace = False

    def verify(self):
        key = VerifyKey(base64.b64decode(PUBLIC_KEY_B64))
        payload = json.dumps(
            self.license, sort_keys=True, separators=(",", ":")
        ).encode()

        key.verify(payload, self.signature)
        self._check_binding()
        self._check_expiry()

    def _check_binding(self):
        expected = self.license.get("bound_to")
        if expected:
            actual = machine_fingerprint(self.license.get("customer_id", ""))
            if actual != expected:
                raise RuntimeError("License not valid for this machine")

    def _check_expiry(self):
        today = datetime.date.today()
        expires = datetime.date.fromisoformat(self.license["expires_at"])
        grace = self.license.get("grace_days", 0)

        if today <= expires:
            return
        if today <= expires + datetime.timedelta(days=grace):
            self.in_grace = True
            return
        raise RuntimeError("KafkaGraph license expired")

    def limits(self):
        return self.license.get("limits", {})

    def features(self):
        return self.license.get("features", {})

    def has_feature(self, f):
        return bool(self.features().get(f, False))
