from dataclasses import dataclass
from typing import Dict
from confluent_kafka.avro import AvroProducer
from avro.schema import parse
from avro.io import DatumWriter
from confluent_kafka.avro import AvroProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from typing import Any

@dataclass
class DownloadEvent:
    """
    Represents a download event.

    Attributes:
        name (str): The name of the download.
        category (str): The category of the download.
        tags (str): The tags associated with the download.
        content_path (str): The path to the content of the download.
        root_path (str): The root path of the download.
        save_path (str): The path where the download is saved.
        total_files (int): The number of files in the download.
        torrent_size (int): The size of the download in bytes.
        current_tracker (str): The current tracker of the download.
        info_hash_v1 (str): The info hash v1 of the download.
        info_hash_v2 (str): The info hash v2 of the download.
        torrent_id (str): The ID of the download.
        finished (bool): Indicates whether the download has finished downloading.
    """
    name: str
    category: str
    tags: str
    content_path: str
    root_path: str
    save_path: str
    total_files: int
    torrent_size: int
    current_tracker: str
    info_hash_v1: str
    info_hash_v2: str
    torrent_id: str
    finished: bool

    def to_dict(self) -> Dict[str, str]:
        """
        Converts the DownloadEvent object to a dictionary.

        Returns:
            dict: A dictionary representation of the DownloadEvent object.
        """
        return {
            "name": self.name,
            "category": self.category,
            "tags": self.tags,
            "content_path": self.content_path,
            "root_path": self.root_path,
            "save_path": self.save_path,
            "total_files": self.total_files,
            "torrent_size": self.torrent_size,
            "current_tracker": self.current_tracker,
            "info_hash_v1": self.info_hash_v1,
            "info_hash_v2": self.info_hash_v2,
            "torrent_id": self.torrent_id,
            "finished": self.finished
        }

def produce_to_topic(bootstrap_servers: str, schema_registry_url: str, topic: str, value: Any, schema_subject: str):
    """
    Produces a value to a Kafka topic using Avro serialization and schema validation.

    Args:
        bootstrap_servers (str): The list of Kafka bootstrap servers.
        schema_registry_url (str): The URL of the schema registry.
        topic (str): The Kafka topic to produce the value to.
        value (Any): The value to produce.
        schema_subject (str): The subject of the Avro schema in the schema registry.
    """

    # Create a CachedSchemaRegistryClient instance
    schema_registry_client = SchemaRegistryClient({'url': schema_registry_url})

    # Get the latest version of the schema for the specified subject
    schema = schema_registry_client.get_latest_version(schema_subject)

    avro_schema = parse(schema.schema.schema_str)

    producer = AvroProducer({
        'bootstrap.servers': bootstrap_servers,
        'schema.registry.url': schema_registry_url
    }, default_value_schema=avro_schema, value_serializer=DatumWriter().write)

    try:
        producer.produce(topic=topic, value=value)
        producer.flush()
    finally:
        producer.close()
