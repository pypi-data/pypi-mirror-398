# opticedge_cloud_utils/pub.py
import json
import traceback
from google.cloud import pubsub_v1
from typing import Any, Dict

_publisher_client = None

def _get_publisher():
    global _publisher_client
    if _publisher_client is None:
        _publisher_client = pubsub_v1.PublisherClient()
    return _publisher_client


def _topic_path_for(publisher: pubsub_v1.PublisherClient, project: str, topic: str) -> str:
    """Get topic path. Uses module publisher for testability/simplicity."""
    if not project:
        raise RuntimeError("Project id not found")
    return publisher.topic_path(project, topic)


def publish_message(project_id: str, topic_name: str, envelope: Dict[str, Any]) -> str:
    if not project_id:
        raise ValueError("project_id not set")

    try:
        publisher = _get_publisher()
        topic = _topic_path_for(publisher, project_id, topic_name)
    except Exception as e:
        print(f"ERROR: topic setup failed: {e}\n{traceback.format_exc()}")
        raise

    try:
        future = publisher.publish(topic, data=json.dumps(envelope).encode("utf-8"))
        msg_id = future.result()
        print(f"INFO: Pub/Sub publish topic={topic} msg_id: {msg_id}")
        return msg_id
    except Exception as e:
        print(f"ERROR: publish failed: {e}\n{traceback.format_exc()}")
        raise
