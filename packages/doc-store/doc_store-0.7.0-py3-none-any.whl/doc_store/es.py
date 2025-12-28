import json
import random
import time

from elasticsearch import Elasticsearch

from .config import config

MAX_DOC_SIZE = 5 << 20  # 5MiB
FLUSH_SIZE = 1 << 20  # 1MiB
FLUSH_COUNT = 200
MAX_RETRIES = 10


def get_es_client() -> Elasticsearch:
    if not config.es.endpoints:
        raise Exception(f"ES endpoints is null or empty")

    es_endpoints = [*config.es.endpoints]
    random.shuffle(es_endpoints)

    return Elasticsearch(
        hosts=es_endpoints,
        basic_auth=(
            config.es.username,
            config.es.password,
        ),
    )


class EsBulkWriter:
    """CAUTION: Not thread-safe."""

    def __init__(
        self,
        client: Elasticsearch,
        index: str | None = None,
        create=False,
        upsert=True,
        ignore_error=False,
        skip_large_doc=False,
        max_doc_size=MAX_DOC_SIZE,
        flush_size=FLUSH_SIZE,
        flush_count=FLUSH_COUNT,
        max_retries=MAX_RETRIES,
    ) -> None:
        self.client = client
        self.index = index
        self.buffer = []
        self.buffer_size = 0
        self.create = create
        self.upsert = upsert
        self.ignore_error = ignore_error
        self.skip_large_doc = skip_large_doc
        self.max_doc_size = max_doc_size
        self.flush_size = flush_size
        self.flush_count = flush_count
        self.max_retries = max_retries
        self.conflict_count = 0
        self.skip_large_count = 0

    def write(self, id: str, doc: dict, index=None):
        doc_size = len(json.dumps(doc).encode("utf-8"))

        if doc_size > self.max_doc_size:
            if self.ignore_error or self.skip_large_doc:
                self.skip_large_count += 1
                print("### SKIP LARGE DOC ###")
                print(id)
                return
            else:
                raise Exception(f"doc {id} is too large.")

        if not index:
            index = self.index
        if not index:
            raise Exception("missing param [index]")

        if not id:
            self.buffer.append({"index": {"_index": index}})
            self.buffer.append(doc)
        elif self.create:
            self.buffer.append({"create": {"_index": index, "_id": id}})
            self.buffer.append(doc)
        elif self.upsert:
            self.buffer.append({"update": {"_index": index, "_id": id}})
            self.buffer.append({"doc": doc, "doc_as_upsert": True})
        else:
            self.buffer.append({"index": {"_index": index, "_id": id}})
            self.buffer.append(doc)

        # 1MiB or 200 docs.
        self.buffer_size += doc_size
        if self.buffer_size >= self.flush_size or len(self.buffer) >= self.flush_count:
            self.__flush()

    def flush(self):
        if self.buffer_size > 0:
            self.__flush()

    def __flush(self):
        buffer = [*self.buffer]
        retries = 0
        sleep_time = 1
        sleep_time_factor = 1.5

        while True:
            try:
                result = self.client.options(request_timeout=60).bulk(body=buffer)
                if not result.get("errors"):
                    break

                errors = []
                next_buffer = []

                for i, item in enumerate(result.get("items", [])):
                    item = list(item.values())[0]
                    if not item.get("error"):
                        continue
                    error = item["error"]
                    if (
                        self.create
                        and isinstance(error, dict)
                        and "type" in error
                        and error["type"] == "version_conflict_engine_exception"
                    ):
                        self.conflict_count += 1
                        continue
                    errors.append(str(error))
                    next_buffer.append(buffer[i * 2])
                    next_buffer.append(buffer[(i * 2) + 1])

                if not next_buffer:
                    break

            except Exception as e:
                errors = [str(e)]
                next_buffer = buffer

            if retries >= self.max_retries:
                error_msg = "ES ERROR: " + "\n".join([str(e) for e in errors])
                print("### BUFFER ###")
                print(buffer)
                if self.ignore_error:
                    print("### ES ERROR ###")
                    print(error_msg)
                    break
                else:
                    raise Exception(error_msg)

            time.sleep(sleep_time)

            for e in errors:
                # has error other than es_rejected_execution_exception.
                if "es_rejected_execution_exception" not in e:
                    sleep_time = sleep_time * sleep_time_factor
                    retries += 1
                    break

            buffer = next_buffer

        self.buffer.clear()
        self.buffer_size = 0
