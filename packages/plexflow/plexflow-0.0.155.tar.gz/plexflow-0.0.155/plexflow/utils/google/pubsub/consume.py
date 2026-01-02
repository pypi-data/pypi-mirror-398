from google.cloud import pubsub_v1
import json

def consume_message(topic_id: str, project_id: str, as_json: bool = True, timeout: int = 5):
    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(project_id, topic_id)

    data = None

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        nonlocal data

        print(f"Received {message}.")
        print(message.data.decode())
        if as_json:
            data = json.loads(message.data.decode())
        else:
            data = message.data.decode()

        message.ack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.
    
    return data