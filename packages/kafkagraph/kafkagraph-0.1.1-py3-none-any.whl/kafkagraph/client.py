from kafkagraph.core.engine import IngestionEngine

class KafkaGraph:
    def __init__(
        self,
        *,
        license_file: str = None,
        api_key: str = None,
        kafka_config: dict,
        neo4j_config: dict,
        topics_config_path: str,
        batch_size: int = 500
    ):
        self.engine = IngestionEngine(
            license_file=license_file,
            api_key=api_key,
            kafka_config=kafka_config,
            neo4j_config=neo4j_config,
            topics_config_path=topics_config_path,
            batch_size=batch_size
        )

    def start(self):
        self.engine.run()

    def stop(self):
        self.engine.shutdown()
