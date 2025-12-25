from __future__ import annotations
import threading
import time
from typing import Dict, Any, Optional, Tuple
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 5000  # sensible default

class MongoCache:
    """
    Very small thread-safe cache for pymongo.MongoClient instances keyed by (uri + client kwargs).
    Re-uses MongoClient (and its internal connection pool) for performance.

    Usage:
        mongo = MongoCache()
        db = mongo.get_db("mongodb+srv://user:pass@host", "mydb")
        col = db.mycol
        ...
        mongo.close_all()
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> (MongoClient, created_ts)
        self._clients: Dict[str, Tuple[MongoClient, float]] = {}

    def _make_key(self, uri: str, kwargs: Dict[str, Any]) -> str:
        if not kwargs:
            return uri
        items = tuple(sorted(kwargs.items()))
        return f"{uri}::{items!r}"

    def get_client(self, uri: str, validate: bool = False, **client_kwargs) -> MongoClient:
        """
        Return a cached MongoClient for the given URI (create if missing).
        validate: if True, attempt a lightweight ping after creating the client to ensure connectivity.
                  (Avoid calling validate=True on every request in high-throughput paths.)
        client_kwargs: forwarded to MongoClient (e.g., maxPoolSize, tls, etc.)
        """
        key = self._make_key(uri, client_kwargs)

        with self._lock:
            entry = self._clients.get(key)
            if entry:
                client, _ = entry
                return client

            # ensure serverSelectionTimeoutMS default unless caller provided it
            if "serverSelectionTimeoutMS" not in client_kwargs:
                client_kwargs["serverSelectionTimeoutMS"] = _DEFAULT_SERVER_SELECTION_TIMEOUT_MS

            client = MongoClient(uri, **client_kwargs)
            created_ts = time.time()
            self._clients[key] = (client, created_ts)

        if validate:
            # do ping outside the lock to avoid blocking other threads
            try:
                client.admin.command("ping")
            except PyMongoError:
                # if validation fails, close client and remove from cache
                with self._lock:
                    # remove only if still same object (race-safe)
                    current = self._clients.get(key)
                    if current and current[0] is client:
                        self._clients.pop(key, None)
                try:
                    client.close()
                except Exception:
                    pass
                raise

        return client

    def get_db(self, uri: str, dbname: str, validate: bool = False, **client_kwargs):
        """
        Convenience to get a Database object from a cached client.
        """
        client = self.get_client(uri, validate=validate, **client_kwargs)
        return client[dbname]

    def close(self, uri: str, **client_kwargs) -> None:
        """
        Close and remove a cached client for the given uri+client_kwargs.
        """
        key = self._make_key(uri, client_kwargs)
        with self._lock:
            entry = self._clients.pop(key, None)
        if entry:
            client, _ = entry
            try:
                client.close()
            except Exception:
                pass

    def close_all(self) -> None:
        """Close all clients in the cache."""
        with self._lock:
            items = list(self._clients.items())
            self._clients.clear()
        for _, (client, _) in items:
            try:
                client.close()
            except Exception:
                pass

    def info(self) -> Dict[str, Any]:
        """
        Simple diagnostics: returns keys and creation timestamps (unix epoch seconds).
        """
        with self._lock:
            return {k: {"created_ts": v[1]} for k, v in self._clients.items()}
