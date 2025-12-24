from kafkagraph.license.rate_limiter import RateLimiter
from kafkagraph.license.features import Feature
from kafkagraph.license.api_keys import load_api_keys

class ApiKeyManager:
    def __init__(self, api_key):
        keys = load_api_keys()
        if api_key not in keys:
            raise RuntimeError("Invalid API key")
        self.limits = {
            "messages_per_second": 50,
            "messages_per_minute": 1000,
            "max_partitions_total": 10,
            "max_partitions_per_topic": 5
        }
        self.features_map = {
            Feature.SIMPLE_MAPPING.value: True,
            Feature.AUTOGRAPH.value: False,
            Feature.SEQUENCE_ARRAY.value: True,
            Feature.TEMPORAL.value: False,
            Feature.DLQ.value: False
        }
        self.rate = RateLimiter(
            self.limits["messages_per_second"],
            self.limits["messages_per_minute"]
        )

    def enforce_rate(self):
        if not self.rate.allow(1):
            raise RuntimeError("Throughput limit exceeded")

    def has_feature(self, feature: Feature):
        return bool(self.features_map.get(feature.value, False))

    def partition_limits(self):
        return {
            "total": self.limits["max_partitions_total"],
            "per_topic": self.limits["max_partitions_per_topic"]
        }
