# tests/test_mongo.py
import importlib
from unittest.mock import patch, MagicMock
import pytest

MODULE_PATH = "opticedge_cloud_utils.mongo"


@pytest.fixture
def module():
    """Import a fresh copy of the module and ensure _mongo_client is cleared."""
    # ensure fresh import
    if MODULE_PATH in globals():
        globals().pop(MODULE_PATH)
    mod = importlib.import_module(MODULE_PATH)
    # clear any cached client
    if hasattr(mod, "_mongo_client"):
        mod._mongo_client = None
    yield mod
    # teardown: clear and reload
    if hasattr(mod, "_mongo_client"):
        mod._mongo_client = None
    importlib.reload(mod)


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_creates_client_and_pings(mock_mongo_client_cls, mock_get_secret, module):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    client = module.get_mongo_client(project_id="test-project", uri_secret="mongo-uri")

    mock_get_secret.assert_called_once_with("test-project", "mongo-uri")
    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    fake_client.admin.command.assert_called_once_with("ping")

    assert client is fake_client
    assert module._mongo_client is fake_client


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_returns_cached_client_on_subsequent_calls(
    mock_mongo_client_cls, mock_get_secret, module
):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    first = module.get_mongo_client(project_id="test-project", uri_secret="mongo-uri")
    second = module.get_mongo_client(project_id="test-project", uri_secret="mongo-uri")

    mock_get_secret.assert_called_once_with("test-project", "mongo-uri")
    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    assert first is second
    assert module._mongo_client is first


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_ping_failure_raises_and_does_not_cache(
    mock_mongo_client_cls, mock_get_secret, module
):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    bad_client = MagicMock()
    bad_client.admin.command.side_effect = Exception("ping failed")
    mock_mongo_client_cls.return_value = bad_client

    with pytest.raises(Exception) as excinfo:
        module.get_mongo_client(project_id="test-project", uri_secret="mongo-uri")

    mock_get_secret.assert_called_once_with("test-project", "mongo-uri")
    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    bad_client.admin.command.assert_called_once_with("ping")

    # module should not cache the bad client
    assert module._mongo_client is None
    assert "ping failed" in str(excinfo.value)


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_creates_client_and_pings(mock_mongo_client_cls, module):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    client = module.get_mongo_client_with_uri(fake_uri)

    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    fake_client.admin.command.assert_called_once_with("ping")

    assert client is fake_client
    assert module._mongo_client is fake_client


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_returns_cached_client_on_subsequent_calls(
    mock_mongo_client_cls, module
):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    first = module.get_mongo_client_with_uri(fake_uri)
    second = module.get_mongo_client_with_uri(fake_uri)

    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    assert first is second
    assert module._mongo_client is first


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_ping_failure_raises_and_does_not_cache(
    mock_mongo_client_cls, module
):
    fake_uri = "mongodb://user:pass@host:27017"

    bad_client = MagicMock()
    bad_client.admin.command.side_effect = Exception("ping failed")
    mock_mongo_client_cls.return_value = bad_client

    with pytest.raises(Exception) as excinfo:
        module.get_mongo_client_with_uri(fake_uri)

    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    bad_client.admin.command.assert_called_once_with("ping")

    # module should not cache the bad client
    assert module._mongo_client is None
    assert "ping failed" in str(excinfo.value)


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_db_returns_database_object(mock_mongo_client_cls, mock_get_secret, module):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_db = MagicMock(name="fake_db")
    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    fake_client.__getitem__.return_value = fake_db
    mock_mongo_client_cls.return_value = fake_client

    db = module.get_mongo_db(db_name="opticedge", project_id="test-project", uri_secret="mongo-uri")
    assert db is fake_db
    fake_client.__getitem__.assert_called_once_with("opticedge")
    mock_get_secret.assert_called_once_with("test-project", "mongo-uri")


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_db_with_uri_returns_database_object(mock_mongo_client_cls, module):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_db = MagicMock(name="fake_db")
    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    fake_client.__getitem__.return_value = fake_db
    mock_mongo_client_cls.return_value = fake_client

    db = module.get_mongo_db_with_uri(uri=fake_uri, db_name="opticedge")
    assert db is fake_db
    fake_client.__getitem__.assert_called_once_with("opticedge")
    mock_mongo_client_cls.assert_called_once_with(fake_uri)


def test_cached_client_shared_between_secret_and_uri_calls(module):
    """If a client is cached by one helper, the other helper should return the same cached client."""
    # Prepare a fake client and set it into the module cache directly
    fake_client = MagicMock()
    module._mongo_client = fake_client

    # Now call both functions; neither should attempt to create a new client
    # Patch MongoClient/get_secret to detect if they would be called
    with patch(f"{MODULE_PATH}.MongoClient") as mock_mongo_client_cls, \
         patch(f"{MODULE_PATH}.get_secret") as mock_get_secret:
        client_from_secret = module.get_mongo_client(project_id="ignored", uri_secret="ignored")
        client_from_uri = module.get_mongo_client_with_uri("ignored-uri")

        assert client_from_secret is fake_client
        assert client_from_uri is fake_client

        mock_mongo_client_cls.assert_not_called()
        mock_get_secret.assert_not_called()
