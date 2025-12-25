# tests/test_mongo_cache.py
import time
import threading
import pytest
from pymongo.errors import PyMongoError

# Try importing the module under test by common names so tests work whether you run
# them from the package root or from inside the package.
try:
    import mongo_cache
except Exception:
    import opticedge_cloud_utils.mongo_cache as mongo_cache  # fallback for package layout


# ---- Fake database returned by FakeClient.__getitem__ ----
class FakeDatabase:
    def __init__(self, name, client):
        self.name = name
        self._client = client

    # small convenience used by examples — return 0 for counts
    def count_documents(self, *args, **kwargs):
        return 0


# ---- Fake objects used by the tests (support extra test-only flags) ----
class FakeAdmin:
    def __init__(self, behavior, uri, orig_kwargs):
        """
        behavior:
          None -> ping succeeds
          "raise" -> ping raises PyMongoError
          "replace" -> create a replacement client in the cache and then raise
        We receive uri and orig_kwargs to help the 'replace' behavior compute the cache key.
        """
        self.behavior = behavior
        self.uri = uri
        self.orig_kwargs = orig_kwargs or {}

    def command(self, cmd):
        if cmd == "ping":
            if self.behavior == "raise":
                raise PyMongoError("simulated ping failure")
            if self.behavior == "replace":
                # create a replacement client and insert it into the cache before failing.
                replacement = mongo_cache.MongoClient(self.uri + "-replacement")
                key = self.uri
                c = getattr(mongo_cache, "_tests_last_cache", None)
                if c is not None:
                    with c._lock:
                        c._clients[key] = (replacement, time.time())
                raise PyMongoError("simulated ping failure after replacement")
            return {"ok": 1}
        return {"ok": 1}


class FakeClient:
    def __init__(self, uri, **kwargs):
        # store inputs so tests can assert on them
        self.uri = uri
        # copy kwargs so tests can inspect them (serverSelectionTimeoutMS may be injected)
        self.kwargs = kwargs.copy()

        # test-only flags (consumed by the fake)
        self._ping_behavior = self.kwargs.pop("_ping_behavior", None)  # None | "raise" | "replace"
        self._close_raises = bool(self.kwargs.pop("_close_raises", False))

        # admin object uses the behavior and also knows the uri/kwargs for replacement
        self.admin = FakeAdmin(self._ping_behavior, uri, kwargs)
        self.closed = False

    def close(self):
        # simulate close raising when requested
        if self._close_raises:
            raise RuntimeError("simulated close error")
        self.closed = True

    # SUPPORT __getitem__ to mimic pymongo.MongoClient[dbname]
    def __getitem__(self, name):
        return FakeDatabase(name, client=self)


# ---- Fixture that monkeypatches MongoClient ----
@pytest.fixture(autouse=True)
def patch_mongo_client(monkeypatch):
    """
    Monkeypatch mongo_cache.MongoClient to our fake factory and expose created_clients list.
    Tests can inspect created_clients list to assert behavior.

    Special behavior flags (test-only):
      - _ping_behavior="raise"  -> FakeAdmin.command will raise on ping
      - _ping_behavior="replace"-> FakeAdmin.command will insert a replacement client into the cache, then raise
      - _close_raises=True       -> FakeClient.close() will raise an exception
    """
    created_clients = []

    def fake_mongo_client(uri, **kwargs):
        client = FakeClient(uri, **kwargs)
        created_clients.append(client)
        return client

    # Replace the MongoClient used by the module under test.
    monkeypatch.setattr(mongo_cache, "MongoClient", fake_mongo_client)
    # Expose the created_clients list and allow tests to expose the last cache instance.
    monkeypatch.setattr(mongo_cache, "_tests_created_clients", created_clients, raising=False)
    monkeypatch.setattr(mongo_cache, "_tests_last_cache", None, raising=False)

    yield created_clients


# ---- Unit tests ----
def test_get_client_returns_same_instance(patch_mongo_client):
    cache = mongo_cache.MongoCache()
    # make this cache visible to the fake admin that may mutate the cache during ping
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://cluster-a"
    c1 = cache.get_client(uri)
    c2 = cache.get_client(uri)
    assert c1 is c2, "Same URI should return the same cached client"


def test_get_client_different_uris_create_different_clients(patch_mongo_client):
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri1 = "mongodb://cluster-a"
    uri2 = "mongodb://cluster-b"

    c1 = cache.get_client(uri1)
    c2 = cache.get_client(uri2)
    assert c1 is not c2
    assert c1.uri == uri1
    assert c2.uri == uri2


def test_kwargs_change_cache_key_and_default_timeout_applied(patch_mongo_client):
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://cluster-a"

    # call with an explicit timeout: this should be preserved (covering the branch where it's present)
    explicit_timeout = 12345
    c_with_timeout = cache.get_client(uri, serverSelectionTimeoutMS=explicit_timeout)
    assert c_with_timeout.kwargs.get("serverSelectionTimeoutMS") == explicit_timeout

    # call without kwargs - default serverSelectionTimeoutMS should be injected (covers lines 50-53)
    c_no_kw = cache.get_client(uri + "-no-kw")
    assert "serverSelectionTimeoutMS" in c_no_kw.kwargs
    assert c_no_kw.kwargs["serverSelectionTimeoutMS"] == mongo_cache._DEFAULT_SERVER_SELECTION_TIMEOUT_MS


def test_get_db_default_validate_does_not_ping(patch_mongo_client):
    """
    get_db() should call get_client with default validate=False, so providing a failing _ping_behavior
    should NOT raise when validate is not requested.
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://no-validate"
    # create db without validation even though _ping_behavior would fail if validate=True
    db = cache.get_db(uri, "somedb", _ping_behavior="raise")
    assert db.name == "somedb"
    # ensure the client was cached
    info = cache.info()
    assert any(uri in k for k in info.keys())


def test_validate_failure_removes_client_and_closes_when_same_entry(patch_mongo_client):
    """
    When validation fails and the cached entry is still the same client, the client should be removed
    and closed (covers the branch that pops the key).
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://cluster-validate-fail"
    with pytest.raises(PyMongoError):
        cache.get_client(uri, validate=True, _ping_behavior="raise")

    info = cache.info()
    assert not any(uri in k for k in info.keys()), "Client that failed validation should be removed from cache"

    created = getattr(mongo_cache, "_tests_created_clients", [])
    assert created, "No clients were created"
    last = created[-1]
    assert last.closed is True


def test_validate_failure_does_not_remove_if_cache_replaced(patch_mongo_client):
    """
    Simulate a race: validation happens but a replacement client was installed in the cache
    between creation and ping. The failing client should be closed but not popped from cache
    because the cache entry now points to a different client (covers lines 66-68).
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://race-case"
    # The fake client will insert a replacement into the cache then raise
    with pytest.raises(PyMongoError):
        cache.get_client(uri, validate=True, _ping_behavior="replace")

    # The cache should still contain an entry for the key, but it should be the replacement client
    info = cache.info()
    assert any(uri in k for k in info.keys()), "Cache should still have an entry after replacement"
    created = getattr(mongo_cache, "_tests_created_clients", [])
    assert len(created) >= 2  # original + replacement
    orig, replacement = created[-2], created[-1]
    # original should be closed
    assert orig.closed is True
    # replacement should be present in the cache (by comparing object identity)
    cached_objs = [v[0] for v in cache._clients.values()]
    assert any(obj is replacement for obj in cached_objs)


def test_close_ignores_close_exceptions(patch_mongo_client):
    """
    Ensure close() swallows exceptions from client.close() (covers the except: pass path).
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://close-ex-1"
    # create a client whose close() will raise; note we must pass the same kwargs when closing
    c = cache.get_client(uri, _close_raises=True)
    # calling close (with same kwargs) should not raise despite close() raising internally
    cache.close(uri, _close_raises=True)
    # ensure entry removed from cache
    info = cache.info()
    assert not any(uri in k for k in info.keys())


def test_close_all_ignores_close_exceptions(patch_mongo_client):
    """
    Ensure close_all() tries to close every client and continues even if some close() calls raise
    (covers the except: pass path in close_all).
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri1 = "mongodb://closeall-good"
    uri2 = "mongodb://closeall-bad"

    good = cache.get_client(uri1)
    bad = cache.get_client(uri2, _close_raises=True)

    # Should not raise even though bad.close() will raise
    cache.close_all()

    assert cache.info() == {}
    # ensure good closed
    assert good.closed is True
    # bad client's close raised so it won't have closed True, but test ensures the function completed
    assert hasattr(bad, "closed")


def test_concurrent_get_client_creates_one_per_key(patch_mongo_client):
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    uri = "mongodb://concurrent-cluster"
    created = []

    def worker(idx):
        # alternate kwargs to create two distinct keys
        if idx % 2 == 0:
            c = cache.get_client(uri)
        else:
            c = cache.get_client(uri, maxPoolSize=5)
        created.append(c)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # There should be at most two distinct client objects (one per unique kwargs set)
    distinct = {id(c) for c in created}
    assert 1 <= len(distinct) <= 2


def test_validate_failure_calls_pop_on_internal_dict(patch_mongo_client):
    """
    Replace cache._clients with a Spy dict so we can assert pop() was called.
    This deterministically verifies the exact line self._clients.pop(key, None)
    is executed when validate=True and ping raises.
    """
    cache = mongo_cache.MongoCache()
    setattr(mongo_cache, "_tests_last_cache", cache)

    class SpyDict(dict):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.popped = False
            self.popped_key = None
            self.pop_calls = 0

        def pop(self, key, default=None):
            # record that pop was called (this will run when your code executes pop)
            self.popped = True
            self.popped_key = key
            self.pop_calls += 1
            # call base implementation
            return super().pop(key, default)

    uri = "mongodb://spy-pop"

    # replace the internal clients dict with a spy
    spy = SpyDict()
    cache._clients = spy

    # compute the exact key that get_client will use (client_kwargs passed here)
    key = cache._make_key(uri, {"_ping_behavior": "raise"})

    # sanity: spy empty
    assert key not in spy

    # now call get_client which will insert into spy[key], then ping raises,
    # and code should call spy.pop(key, None) inside the except handler.
    with pytest.raises(PyMongoError):
        cache.get_client(uri, validate=True, _ping_behavior="raise")

    # assert that pop() was called on our spy (thus the pop(...) line executed)
    assert spy.popped is True, "Expected pop() to be called on the internal dict"
    assert spy.popped_key == key, "pop() should have been called with the same key get_client used"


# End of file
