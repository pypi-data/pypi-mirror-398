from kafkagraph.license.signed import SignedLicense
from kafkagraph.license.rate_limiter import RateLimiter
from kafkagraph.license.features import Feature

class LicenseManager:
    def __init__(self, license_file):
        self.license = SignedLicense(license_file)
        self.license.verify()
        self.limits = self.license.limits()
        self.rate = RateLimiter(
            self.limits.get("messages_per_second"),
            self.limits.get("messages_per_minute")
        )

    def enforce_rate(self):
        if not self.rate.allow(1):
            raise RuntimeError("Throughput limit exceeded")

    def has_feature(self, feature: Feature):
        return self.license.has_feature(feature.value)

    def partition_limits(self):
        return {
            "total": self.limits.get("max_partitions_total"),
            "per_topic": self.limits.get("max_partitions_per_topic")
        }
