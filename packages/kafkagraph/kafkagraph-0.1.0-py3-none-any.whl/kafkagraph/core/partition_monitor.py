from collections import defaultdict

class PartitionMonitor:
    def __init__(self, license_mgr):
        self.license_mgr = license_mgr
        self.assignments = defaultdict(set)

    def on_partitions_assigned(self, consumer, partitions):
        self.assignments.clear()
        for tp in partitions:
            self.assignments[tp.topic].add(tp.partition)

        limits = self.license_mgr.partition_limits()
        total = sum(len(v) for v in self.assignments.values())

        if limits["total"] and total > limits["total"]:
            raise RuntimeError("Partition limit exceeded")

        if limits["per_topic"]:
            for t, p in self.assignments.items():
                if len(p) > limits["per_topic"]:
                    raise RuntimeError(f"Partition limit exceeded for {t}")
