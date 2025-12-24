from kafka import KafkaConsumer
import json

def create_consumer(cfg, topics, listener):
    consumer = KafkaConsumer(
        bootstrap_servers=cfg["brokers"],
        group_id=cfg["group_id"],
        auto_offset_reset=cfg.get("auto_offset_reset", "earliest"),
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode())
    )
    consumer.subscribe(topics=topics, listener=listener)
    return consumer
