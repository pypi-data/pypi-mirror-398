# tests/test_pub.py
import pytest
from unittest.mock import MagicMock

import opticedge_cloud_utils.pub as pubsub_client


def test__topic_path_for_returns_expected():
    class FakePublisher:
        def topic_path(self, project: str, topic: str) -> str:
            return f"projects/{project}/topics/{topic}"

    path = pubsub_client._topic_path_for(FakePublisher(), "my-project", "my-topic")
    assert path == "projects/my-project/topics/my-topic"


@pytest.mark.parametrize("bad_project", ("", None))
def test__topic_path_for_raises_when_no_project(bad_project):
    class FakePublisher:
        def topic_path(self, project: str, topic: str) -> str:
            return f"projects/{project}/topics/{topic}"

    with pytest.raises(RuntimeError):
        pubsub_client._topic_path_for(FakePublisher(), bad_project, "topic-name")


def test__get_publisher_initializes_singleton(monkeypatch):
    monkeypatch.setattr(pubsub_client, "_publisher_client", None, raising=False)

    class DummyPublisher:
        instances = 0

        def __init__(self):
            DummyPublisher.instances += 1

    monkeypatch.setattr(pubsub_client.pubsub_v1, "PublisherClient", DummyPublisher)

    p1 = pubsub_client._get_publisher()
    p2 = pubsub_client._get_publisher()

    assert p1 is p2
    assert DummyPublisher.instances == 1
    assert pubsub_client._publisher_client is p1


def test__get_publisher_returns_cached_instance(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(pubsub_client, "_publisher_client", sentinel, raising=False)

    monkeypatch.setattr(
        pubsub_client.pubsub_v1,
        "PublisherClient",
        lambda *a, **k: pytest.fail("PublisherClient should not be called"),
    )

    assert pubsub_client._get_publisher() is sentinel


def test_publish_message_success(monkeypatch):
    fake_future = MagicMock()
    fake_future.result.return_value = "msg-id-123"

    fake_publisher = MagicMock()
    fake_publisher.publish.return_value = fake_future

    monkeypatch.setattr(pubsub_client, "_get_publisher", lambda: fake_publisher)
    monkeypatch.setattr(pubsub_client, "_topic_path_for", lambda *a, **k: "projects/p/topics/t")

    msg_id = pubsub_client.publish_message("project-id", "topic-name", {"a": 1})

    assert msg_id == "msg-id-123"
    fake_publisher.publish.assert_called_once()


def test_publish_message_raises_when_no_project():
    with pytest.raises(ValueError):
        pubsub_client.publish_message("", "topic", {})


def test_publish_message_raises_on_publish_error(monkeypatch):
    fake_publisher = MagicMock()
    fake_publisher.publish.side_effect = RuntimeError("boom")

    monkeypatch.setattr(pubsub_client, "_get_publisher", lambda: fake_publisher)
    monkeypatch.setattr(pubsub_client, "_topic_path_for", lambda *a, **k: "projects/p/topics/t")

    with pytest.raises(RuntimeError):
        pubsub_client.publish_message("project", "topic", {})


def test_publish_message_handles_topic_setup_failure(monkeypatch, capsys):
    def fake_get_publisher():
        raise RuntimeError("setup failed")

    monkeypatch.setattr(pubsub_client, "_get_publisher", fake_get_publisher)

    with pytest.raises(RuntimeError):
        pubsub_client.publish_message("project-id", "topic-name", {"a": 1})

    captured = capsys.readouterr()
    assert "topic setup failed" in captured.out
