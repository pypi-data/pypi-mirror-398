import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generator, Iterable, List, Optional

import redis

from .config import config


@dataclass
class StreamMessage:
    stream: str
    id: str
    fields: Dict[str, Any]


class RedisStreamProducer:
    """Generic Redis Stream producer."""

    def __init__(self, client: redis.Redis):
        self.client = client

    def add(self, stream: str, fields: Dict[str, Any], id: str = "*", maxlen: Optional[int] = None) -> str:
        args: Dict[str, Any] = {}
        # Prefer per-call maxlen; otherwise fall back to config.redis.stream_maxlen if set
        effective_maxlen = maxlen if maxlen is not None else config.redis.stream_maxlen
        if effective_maxlen is not None:
            # approximate trimming for performance
            # TODO: 设置队列最大长度，避免队列无限增长
            args["maxlen"] = effective_maxlen
            args["approximate"] = True
        return self.client.xadd(stream, fields, id=id, **args)

    def add_many(self, stream: str, items: Iterable[Dict[str, Any]], maxlen: Optional[int] = None) -> List[str]:
        ids: List[str] = []
        for fields in items:
            ids.append(self.add(stream, fields, maxlen=maxlen))
        return ids


class RedisStreamConsumer:
    """
    Generic Redis Stream consumer for consumer-group based consumption.
    - Auto-generates a unique consumer name per run (overridable via env).
    - Supports XREADGROUP and XAUTOCLAIM for reclaiming stale pending messages.
    - Provides helpers to ack messages and iterate batches with flush timeout.
    """

    def __init__(
        self,
        url: Optional[str],
        stream: str,
        group: str,
        consumer: Optional[str] = None,
        create_group: bool = True,
    ):
        self.client = redis.Redis.from_url(url or config.redis.url, decode_responses=True)
        self.stream = stream
        self.group = group
        self._start_ms = str(datetime.now()).split(".")[0].replace(":", "").replace("-", "").replace(" ", "-")
        self.consumer = consumer or self._generate_consumer_name()
        # default parameters for operations (can be overridden per-call)
        self.default_read_count: int = config.redis.read_count
        self.default_block_ms: int = config.redis.block_ms
        self.default_claim_idle_ms: int = config.redis.claim_idle_ms
        self.default_claim_batch: int = config.redis.claim_batch
        self.default_flush_ms: int = config.redis.flush_ms
        if create_group:
            self.ensure_group()

    def _generate_consumer_name(self) -> str:
        env_id = os.getenv("REDIS_CONSUMER_ID")
        if env_id:
            return str(env_id)
        return f"{socket.gethostname()}-{os.getpid()}-{self._start_ms}"

    def ensure_group(self) -> None:
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def read(
        self,
        count: Optional[int] = None,
        block_ms: Optional[int] = None,
    ) -> List[StreamMessage]:
        if count is None:
            count = self.default_read_count
        if block_ms is None:
            block_ms = self.default_block_ms
        res = self.client.xreadgroup(
            groupname=self.group,
            consumername=self.consumer,
            streams={self.stream: ">"},
            count=count,
            block=block_ms,
        )
        messages: List[StreamMessage] = []
        if not res:
            return messages
        for stream, entries in res:
            for mid, fields in entries:
                messages.append(StreamMessage(stream=stream, id=mid, fields=fields))
        return messages

    def ack(self, ids: Iterable[str]) -> int:
        if not ids:
            return 0
        return int(self.client.xack(self.stream, self.group, *ids))

    def pending_summary(self) -> Dict[str, Any]:
        try:
            pend = self.client.xpending(self.stream, self.group)
            return pend if isinstance(pend, dict) else {"pending": 0}
        except Exception:
            return {"pending": 0}

    def claim_stale(
        self,
        min_idle_ms: Optional[int] = None,
        count: Optional[int] = None,
        start_id: str = "0-0",
    ) -> List[StreamMessage]:
        if min_idle_ms is None:
            min_idle_ms = self.default_claim_idle_ms
        if count is None:
            count = self.default_claim_batch
        res = self.client.xautoclaim(
            name=self.stream,
            groupname=self.group,
            consumername=self.consumer,
            min_idle_time=min_idle_ms,
            start_id=start_id,
            count=count,
        )
        messages: List[StreamMessage] = []
        next_id = start_id
        if isinstance(res, (list, tuple)):
            if len(res) == 3:
                next_id, entries, _deleted = res
            elif len(res) == 2:
                next_id, entries = res
            else:
                entries = []
        else:
            entries = []
        for mid, fields in entries:
            messages.append(StreamMessage(stream=self.stream, id=mid, fields=fields))
        return messages

    def read_or_claim(
        self,
        count: Optional[int] = None,
        prefer_claim: bool = False,
        min_idle_ms: Optional[int] = None,
        block_ms: Optional[int] = None,
    ) -> List[StreamMessage]:
        """
        Fetch up to `count` messages by combining claiming pending and reading new ones.
        - If prefer_claim is True: claim first, then read the remaining.
        - If prefer_claim is False: read first, then claim the remaining.
        Uses default_read_count when `count` is None.
        """
        total = count if count is not None else self.default_read_count
        messages: List[StreamMessage] = []
        effective_block = block_ms if block_ms is not None else self.default_block_ms
        effective_idle = min_idle_ms if min_idle_ms is not None else self.default_claim_idle_ms

        if prefer_claim:
            reclaimed = self.claim_stale(min_idle_ms=effective_idle, count=total)
            if reclaimed:
                messages.extend(reclaimed)
            remaining = max(0, total - len(messages))
            if remaining > 0:
                new_msgs = self.read(count=remaining, block_ms=effective_block)
                if new_msgs:
                    messages.extend(new_msgs)
            return messages
        else:
            new_msgs = self.read(count=total, block_ms=effective_block)
            if new_msgs:
                messages.extend(new_msgs)
            remaining = max(0, total - len(messages))
            if remaining > 0:
                reclaimed = self.claim_stale(min_idle_ms=effective_idle, count=remaining)
                if reclaimed:
                    messages.extend(reclaimed)
            return messages

    def iter_batches(
        self,
        batch_size: int,
        block_ms: Optional[int] = None,
        flush_ms: Optional[int] = None,
        read_count: Optional[int] = None,
        min_idle_reclaim_ms: Optional[int] = None,
        reclaim_count: Optional[int] = None,
    ) -> Generator[List[StreamMessage], None, None]:
        """
        Yield lists of StreamMessage with size up to batch_size. Flush if idle for flush_ms.
        Optionally try to reclaim stale messages before reading new ones.
        """
        buffer: List[StreamMessage] = []
        last_flush = time.time()
        # time-based flush
        flush_threshold = flush_ms if flush_ms is not None else self.default_flush_ms
        while True:
            if min_idle_reclaim_ms is not None:
                reclaimed = self.claim_stale(
                    min_idle_ms=min_idle_reclaim_ms,
                    count=(reclaim_count if reclaim_count is not None else self.default_claim_batch),
                )
                if reclaimed:
                    buffer.extend(reclaimed)
                    if len(buffer) >= batch_size:
                        yield buffer[:batch_size]
                        buffer = buffer[batch_size:]
                        last_flush = time.time()
                        continue

            msgs = self.read(
                count=(read_count if read_count is not None else batch_size),
                block_ms=(block_ms if block_ms is not None else self.default_block_ms),
            )
            if msgs:
                buffer.extend(msgs)
                if len(buffer) >= batch_size:
                    yield buffer[:batch_size]
                    buffer = buffer[batch_size:]
                    last_flush = time.time()
                    continue

            if (time.time() - last_flush) * 1000.0 >= flush_threshold:
                if buffer:
                    yield buffer
                    buffer = []
                    last_flush = time.time()
                else:
                    break


class RedisStreamManager:
    def __init__(self, client: redis.Redis):
        self.client = client

    def stream_info(self, stream: str, full: bool = False, count: Optional[int] = None) -> Dict[str, Any]:
        if full:
            return self.client.xinfo_stream(stream, full=True, count=count)
        return self.client.xinfo_stream(stream)

    def groups_info(self, stream: str) -> List[Dict[str, Any]]:
        try:
            return self.client.xinfo_groups(stream)
        except redis.exceptions.ResponseError as e:
            if "no such key" == str(e):
                print(f"stream {stream} not found")
                return []
            else:
                raise e

    def consumers_info(self, stream: str, group: str) -> List[Dict[str, Any]]:
        return self.client.xinfo_consumers(stream, group)

    def length(self, stream: str) -> int:
        return int(self.client.xlen(stream))

    def last_generated_id(self, stream: str) -> Optional[str]:
        try:
            info = self.client.xinfo_stream(stream)
            return info.get("last-generated-id")
        except Exception:
            return None

    def trim_maxlen(self, stream: str, maxlen: int, approximate: bool = True, limit: Optional[int] = None) -> int:
        trimmed = self.client.xtrim(stream, maxlen=maxlen, approximate=approximate, limit=limit)
        return int(trimmed) if isinstance(trimmed, int) else int(trimmed or 0)

    def trim_minid(self, stream: str, minid: str, approximate: bool = True, limit: Optional[int] = None) -> int:
        trimmed = self.client.xtrim(stream, minid=minid, approximate=approximate, limit=limit)
        return int(trimmed) if isinstance(trimmed, int) else int(trimmed or 0)

    def get_lag(self, stream: str, group: str) -> Optional[int]:
        """
        Return group's lag if available (Redis 7+ exposes 'lag' in XINFO GROUPS).
        If not available, returns None.
        """
        try:
            groups = self.client.xinfo_groups(stream)
        except Exception:
            return None
        for g in groups:
            if g.get("name") == group:
                if "lag" in g:
                    try:
                        return int(g["lag"])
                    except Exception:
                        return None
                return None
        return None

    def get_message(self, stream: str, id: str):
        res = self.client.xrange(stream, min=id, max=id, count=1)
        # 格式：[('1640995200000-0', {'field1': 'val1', 'myfield': 'val2'})]
        if not res:
            return None
        return res[0][1]


class RedisStream:
    def __init__(self, url: Optional[str] = None) -> None:
        url = url or config.redis.url
        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.manager = RedisStreamManager(self.client)
        self.producer = RedisStreamProducer(self.client)
        self.consumer_group = config.redis.consumer_group
        self.consumer_pool = {}

    def get_consumer(self, stream: str) -> RedisStreamConsumer:
        key = f"{stream}:{self.consumer_group}"
        if key not in self.consumer_pool:
            self.consumer_pool[key] = RedisStreamConsumer(
                None,
                stream,
                self.consumer_group,
                create_group=True,
            )
        return self.consumer_pool[key]
