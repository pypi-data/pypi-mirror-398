from google.cloud import pubsub_v1
import json

def produce_message(value, topic_id: str, project_id: str, as_json: bool = True):
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(project_id, topic_id)

    if as_json:
        data_str = json.dumps(value)
    else:
        data_str = str(value)

    # Data must be a bytestring
    data = data_str.encode("utf-8")
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data)
    print(future.result())

    print(f"Published messages to {topic_path}.")