import yaml
from kafkagraph.core.consumer import create_consumer
from kafkagraph.core.partition_monitor import PartitionMonitor
from kafkagraph.core.dispatcher import dispatch
from kafkagraph.core.batcher import Batch
from kafkagraph.neo4j.writer import Neo4jWriter
from kafkagraph.license.manager import LicenseManager
from kafkagraph.license.api_key_manager import ApiKeyManager

class IngestionEngine:
    def __init__(
        self,
        license_file,
        api_key,
        kafka_config,
        neo4j_config,
        topics_config_path,
        batch_size
    ):
        if license_file:
            self.license = LicenseManager(license_file)
        elif api_key:
            self.license = ApiKeyManager(api_key)
        else:
            raise RuntimeError("Provide either license_file or api_key")
        self.topics = yaml.safe_load(open(topics_config_path))
        self.writer = Neo4jWriter(neo4j_config)
        self.batch = Batch(batch_size)

        self.partition_monitor = PartitionMonitor(self.license)
        self.consumer = create_consumer(
            kafka_config,
            list(self.topics.keys()),
            self.partition_monitor
        )

        self.running = True

    def run(self):
        for msg in self.consumer:
            if not self.running:
                break

            self.license.enforce_rate()

            cfg = self.topics.get(msg.topic)
            nodes, rels = dispatch(msg.value, cfg, self.license)
            self.batch.add(nodes, rels)

            if self.batch.ready():
                self.writer.write(self.batch.nodes, self.batch.rels)
                self.consumer.commit()
                self.batch.clear()

    def shutdown(self):
        self.running = False
