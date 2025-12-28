import os
import socket

import pymongo

from .config import config
from .json_util import json_dumps
from .utils import get_username

MAX_DOC_SIZE = 5 << 20  # 5MiB
FLUSH_SIZE = 1 << 20  # 1MiB
FLUSH_COUNT = 200
MAX_RETRIES = 10


def get_mongo_client():
    db_uri = config.db.uri
    username = get_username()
    hostname = socket.gethostname()
    pid = os.getpid()
    client = pymongo.MongoClient(
        db_uri,
        appname=f"DocStore({username}@{hostname}:{pid})",
        # Connection Pool settings
        minPoolSize=config.db.min_pool_size,
        maxPoolSize=config.db.max_pool_size,
        maxConnecting=config.db.max_connecting,
        maxIdleTimeMS=config.db.max_idle_time_ms,
        waitQueueTimeoutMS=config.db.wait_queue_timeout_ms,
        # Timeout/Heartbeat settings
        timeoutMS=config.db.timeout_ms,
        socketTimeoutMS=config.db.socket_timeout_ms,
        connectTimeoutMS=config.db.connect_timeout_ms,
        serverSelectionTimeoutMS=config.db.server_selection_timeout_ms,
        heartbeatFrequencyMS=config.db.heartbeat_frequency_ms,
        # Read/Write settings
        readPreference=config.db.read_preference,
        maxStalenessSeconds=config.db.max_staleness_seconds,
    )
    return client


def get_mongo_db():
    client = get_mongo_client()
    return client.get_database()


def get_collection(name: str):
    db = get_mongo_db()
    return db.get_collection(name)


def pool_stats(client: pymongo.MongoClient) -> dict:
    stats = {}
    for addr, server in client._topology._servers.items():
        pool = server._pool
        stats[f"{addr[0]}:{addr[1]}"] = {
            "active_connections": pool.active_sockets,
            "idle_connections": len(pool.conns),
            "pending_connections": pool._pending,
            "active_requests": pool.requests,
            "pending_requests": pool.operation_count - pool.requests,
            "total_requests": pool.operation_count,
        }
    return stats


class MongoBulkWriter:
    """CAUTION: Not thread-safe."""

    def __init__(
        self,
        collection: str,
        upsert=True,
        max_doc_size=MAX_DOC_SIZE,
        flush_size=FLUSH_SIZE,
        flush_count=FLUSH_COUNT,
        # max_retries=MAX_RETRIES,
    ) -> None:
        self.coll = get_collection(collection)
        self.buffer = []
        self.buffer_size = 0
        self.upsert = upsert
        self.max_doc_size = max_doc_size
        self.flush_size = flush_size
        self.flush_count = flush_count

    def write(self, doc: dict, id=None, pk=[]):
        if not id and not pk:
            raise Exception("param id & pk cannot be both empty.")
        if id is not None:
            filter = {"_id": id}
        else:
            filter = {k: doc.get(k) for k in pk}
        if all(v is None for v in filter.values()):
            raise Exception("all filter values are null.")

        doc_str = json_dumps(doc).encode("utf-8")
        doc_size = len(doc_str)
        if doc_size > self.max_doc_size:
            raise Exception(f"doc [{doc_str[:512]}] is too large.")

        self.buffer.append((filter, doc))

        self.buffer_size += doc_size
        if self.buffer_size >= self.flush_size or len(self.buffer) >= self.flush_count:
            self.__flush()

    def flush(self):
        if self.buffer_size > 0:
            self.__flush()

    def __flush(self):
        bulkOps = []
        for filter, doc in self.buffer:
            bulkOps.append(
                pymongo.UpdateOne(
                    filter,
                    {"$set": doc},
                    upsert=True,
                )
            )
        self.coll.bulk_write(bulkOps)
