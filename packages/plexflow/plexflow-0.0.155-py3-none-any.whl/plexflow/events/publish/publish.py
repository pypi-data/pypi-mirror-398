from avro.schema import parse
from avro.io import DatumWriter
from confluent_kafka.avro import AvroProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from typing import Any
import json

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
    }, default_value_schema=avro_schema)

    producer.produce(topic=topic, value=value)
    producer.flush()
