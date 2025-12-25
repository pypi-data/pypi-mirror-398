# opticedge_cloud_utils/pub.py
import json
import traceback
from google.cloud import pubsub_v1
from typing import Any, Dict, Optional

_publisher_client = None

def _topic_path_for(publisher: pubsub_v1.PublisherClient, project: str, topic: str) -> str:
    if not project:
        raise RuntimeError("Project id not found")
    return publisher.topic_path(project, topic)


def _get_publisher():
    global _publisher_client
    if _publisher_client is None:
        _publisher_client = pubsub_v1.PublisherClient()
    return _publisher_client


def publish_message(project_id: str, topic_name: str, envelope: Dict[str, Any]) -> Optional[str]:
    if not project_id:
        print("project_id not set. Skipping publish.")
        return None

    try:
        publisher = _get_publisher()
        topic = _topic_path_for(publisher, project_id, topic_name)
    except Exception as e:
        print(f"ERROR: topic setup failed: {e}\n{traceback.format_exc()}")
        return

    try:
        future = publisher.publish(topic, data=json.dumps(envelope).encode("utf-8"))
        msg_id = future.result()
        return msg_id
    except Exception as e:
        print(f"ERROR: publish failed: {e}\n{traceback.format_exc()}")
        return None
