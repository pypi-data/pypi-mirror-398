from kafka import KafkaConsumer
from kafka.consumer.subscription_state import ConsumerRebalanceListener
import json

class RebalanceListener(ConsumerRebalanceListener):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_partitions_revoked(self, consumer, partitions):
        pass

    def on_partitions_assigned(self, consumer, partitions):
        self.monitor.on_partitions_assigned(consumer, partitions)

def create_consumer(cfg, topics, listener):
    consumer = KafkaConsumer(
        bootstrap_servers=cfg["brokers"],
        group_id=cfg["group_id"],
        auto_offset_reset=cfg.get("auto_offset_reset", "earliest"),
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode())
    )
    rl = listener if isinstance(listener, ConsumerRebalanceListener) else RebalanceListener(listener)
    consumer.subscribe(topics=topics, listener=rl)
    return consumer
