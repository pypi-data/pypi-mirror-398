import hashlib
import io
import json
import os
import random
import re
import socket
import time
import uuid
import warnings
from functools import cached_property, wraps
from typing import Any, Callable, Iterable, Literal, Sequence, TypeVar

import numpy as np
import pymongo.errors
from bson.objectid import ObjectId
from PIL import Image
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.database import Database

from .es import EsBulkWriter, get_es_client
from .interface import (
    AlreadyExistsError,
    AttrInput,
    AttrValueType,
    Block,
    BlockInput,
    Content,
    ContentBlockInput,
    ContentInput,
    Doc,
    DocEvent,
    DocExistsError,
    DocInput,
    DocStoreInterface,
    Element,
    ElementExistsError,
    ElementNotFoundError,
    ElementTagging,
    ElemType,
    EmbeddableElemType,
    Embedding,
    EmbeddingInput,
    EmbeddingModel,
    EmbeddingModelUpdate,
    EmbeddingQuery,
    EvalContent,
    EvalLayout,
    EvalLayoutBlock,
    EvalStatus,
    KnownName,
    KnownNameInput,
    KnownNameUpdate,
    KnownOptionInput,
    Layout,
    LayoutInput,
    MaskBlock,
    MetricInput,
    NotFoundError,
    Page,
    PageInput,
    Q,
    StandaloneBlockInput,
    T,
    TaggingInput,
    Task,
    TaskCount,
    TaskInput,
    TaskMismatchError,
    Trigger,
    TriggerAction,
    TriggerCondition,
    TriggerInput,
    User,
    UserInput,
    UserUpdate,
    Value,
    ValueInput,
)
from .io import read_file
from .kafka import KafkaWriter
from .mongodb import get_mongo_client, pool_stats
from .oid import oid
from .pdf_doc import PDFDocument
from .redis_stream import RedisStream
from .structs import ANGLE_OPTIONS, BLOCK_TYPES, CONTENT_FORMATS
from .utils import encode_ndarray, get_username, normalize_vector, timed_property
from .version import min_required_version
from .version import version as doc_store_version

Image.MAX_IMAGE_PIXELS = None


E = TypeVar("E", bound=Element)


EVENT_PROJECTION = {
    "_id": 0,
    "id": 1,
    "providers": 1,
    "provider": 1,
    "type": 1,
    "versions": 1,
    "version": 1,
    "tags": 1,
}

# Example of tags, attrs and metrics:
# {
#   "tags": [
#     "prefix1__tag1",
#     "prefix2__tag2",
#   ],
#   "attrs": {
#     "attr_name_1": "attr_value_1",
#     "attr_name_2": true,
#     "attr_name_3": ["attr_value_3", "attr_value_4"],
#   },
#   "metrics": {
#     "metric_name_1": 0.1,
#     "metric_name_2": 2,
#   },
# }
#
# Doc {
#   /* ID */
#   "id": "doc-caa42891-d13b-4dbf-ab7c-d2d23f76d770", // the unique doc_id
#
#   "orig_path": "s3://bucket/path/to/document.docx",
#   "orig_filesize": 245267,
#   "orig_hash": "9b1c8ef1309b52a63d457b9fb54d33eaebddf456a489d8da474f742be56467d8",
#
#   "pdf_path": "s3://bucket/path/to/document_1.pdf", (Unique Index)
#   "pdf_filesize": 223245,
#   "pdf_hash": "640b453d6de9d7fa198c6612107865bf2809ad02cea9dc44694fb5c64bde3335", (Unique Index)
#
#   "num_pages": 8,
#
#   /* First Page Info */
#   "page_width": 0,
#   "page_height": 0,
#
#   /* metadata from the pdf file. */
#   "metadata": {
#     "title": "xxxx",
#     "author": "xxxx"
#   },
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Page {
#   /* ID */
#   "id": "page-aac0d7e4-d22d-4b08-a8e8-1be28f79bc06", // the unique page_id
#
#   "doc_id": "e52e94f9-704d-4c8c-b9fc-bb375df705cc", (Index)
#   "page_idx": 0,
#
#   /* Image Info */
#   "image_path": "s3://bucket/path/to/page-image.jpg", (Unique Index)
#   "image_filesize": 134156,
#   "image_hash": "19fca535abe1fefd8e478afaac2f3b42f1d64eeb9e719dfd3ecfeb9789d4fe12",
#   "image_width": 0,
#   "image_height": 0,
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Layout {
#   /* ID */
#   "id": "layout-2b239dce-9c61-4a5d-9e73-1fb6f145eafe", // the unique layout_id
#
#   /* Unique Index */
#   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
#   "provider": "layout__xxx",
#
#   /* Layout Data */
#   /* 使用多叉树，允许块嵌套任意级。 */
#   "blocks": [
#     {
#       "id": "09329d9b-db9d-4c89-a8af-19a179e92890",
#       "type": "title",
#       "bbox": "0.0000,0.0000,1.0000,1.0000",
#       "angle": None,  # enum(None, 0, 90, 180, 270)
#     },
#     { ... },
#     ...
#   ],
#   /* 记录块之间的关系 */
#   "relations": [
#     {
#       "from": "070a408f-3d52-451c-8f95-4cf7a817bc20",
#       "to": "1614e7f7-fdb8-4135-a8b7-f83391008ce6",
#       "relation": "caption_of",
#     },
#     { ... },
#     ...
#   ],
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Block {
#   /* ID */
#   "id": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d", // the unique block_id
#
#   /* Unique Index */
#   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
#   "type": "title",
#   "bbox": "0.0000,0.0000,1.0000,1.0000",
#   "angle": None,  # enum(None, 0, 90, 180, 270)
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Content {
#   /* ID */
#   "id": "content-01a0c73b-c25c-4d5b-a535-5b21c55c5fd3", // the unique content_id
#
#   /* Unique Index */
#   "block_id": "145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
#   "version": "gemini_2_5_pro",
#
#   /* Copied Fields */
#   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
#
#   /* Main Fields */
#   "format": "markdown",
#   "content": "content of the block",
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Value {
#   /* ID */
#   "id": "value-01a0c73b-c25c-4d5b-a535-5b21c55c5fd3", // the unique value_id
#
#   /* Unique Index */
#   "elem_id": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
#   "key": "vit__embed_vector",
#
#   /* Main Fields */
#   "type": "string",  # "string", "vector", (auto-set by insert_value())
#   "value": "This is the value",
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Task {
#   /* ID */
#   "id": "task-dc99b06d-aeb2-4159-a4b9-a2bcf3c26b9b", // the unique task_id
#   "target": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
#   "command": "table_ext",
#   "args": {
#     "model_path": "/path/to/the/model"
#   }
#   "status": "new",  # "new", "done", "error", "skipped"
#   "error_message": "error message if any",
#
#   "create_user": "zhangsan",
#   "create_time": 1749031069945,
#
#   "update_user": "worker-1",
#   "update_time": 1749031069945,
# }
#
# Eval Layout {
#   /* ID */
#   "id": "eval-layout-xxx", // the unique eval_layout_id
#
#   "page_id": "page-xxx",
#   "layout_id": "layout-xxx",
#   "provider": "model__xxx",
#
#   /* Layout Data */
#   "blocks": [...],
#   "relations": [...],
#   "status": "pending",  # "pending", "success", "error"
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Eval Content {
#   /* ID */
#   "id": "eval-content-xxx", // the unique eval_content_id
#
#   "page_id": "page-xxx",
#   "content_id": "content-xxx",
#   "version": "model__xxx",
#   "format": "markdown",
#   "content": "content text",
#   "status": "pending",  # "pending", "success", "error"
#
#   /* Writable Fields */
#   "tags": [...],
#   "attrs": {...},
#   "metrics": {...},
#
#   "create_time": 1749031069945,
#   "update_time": 1749031069945,
# }
#
# Distributed Lock {
#   "key": "page-blocks:145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
#   "version": 1,  # incremented on each write
# }
#
# Distributed Counter {
#   "key": "some-counter-key",
#   "value": 12345,
# }


class DbCollections:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_doc_collection(self, name: str):
        coll = self.db.get_collection(name)
        coll.create_index([("id", 1)], unique=True)
        coll.create_index([("tags", 1)])
        coll.create_index([("attrs.$**", 1)])
        coll.create_index([("metrics.$**", 1)])
        return coll

    @cached_property
    def docs(self):
        coll = self.get_doc_collection("docs")
        coll.create_index([("pdf_path", 1)], unique=True)
        coll.create_index([("pdf_hash", 1)], unique=True)
        return coll

    @cached_property
    def pages(self):
        coll = self.get_doc_collection("pages")
        coll.create_index([("image_path", 1)], unique=True)
        # coll.create_index([("image_hash", 1)], unique=True)
        coll.create_index([("doc_id", 1)])
        coll.create_index([("providers", 1)])
        # TODO: page should have initial category fields.
        return coll

    @cached_property
    def layouts(self):
        coll = self.get_doc_collection("layouts")
        coll.create_index([("page_id", 1), ("provider", 1)], unique=True)
        coll.create_index([("provider", 1)])
        return coll

    @cached_property
    def blocks(self):
        coll = self.get_doc_collection("blocks")
        coll.create_index([("page_id", 1), ("type", 1)])
        coll.create_index([("image_path", 1)])
        coll.create_index([("type", 1)])
        coll.create_index([("versions", 1)])
        return coll

    @cached_property
    def contents(self):
        coll = self.get_doc_collection("contents")
        coll.create_index([("block_id", 1), ("version", 1)], unique=True)
        coll.create_index([("version", 1)])
        coll.create_index([("page_id", 1)])
        return coll

    @cached_property
    def eval_layouts(self):
        coll = self.get_doc_collection("eval_layouts")
        coll.create_index([("layout_id", 1), ("provider", 1)], unique=True)
        coll.create_index([("provider", 1)])
        return coll

    @cached_property
    def eval_contents(self):
        coll = self.get_doc_collection("eval_contents")
        coll.create_index([("content_id", 1), ("version", 1)], unique=True)
        return coll

    @cached_property
    def values(self):
        coll = self.db.get_collection("values")
        coll.create_index([("id", 1)], unique=True)
        coll.create_index([("elem_id", 1), ("key", 1)], unique=True)
        coll.create_index([("key", 1)])
        return coll

    @cached_property
    def tasks(self):
        coll = self.db.get_collection("tasks")
        coll.create_index([("id", 1)], unique=True)
        coll.create_index([("target", 1)])
        coll.create_index([("batch_id", 1)])
        coll.create_index([("status", 1)])
        coll.create_index([("command", 1), ("status", 1)])
        coll.create_index([("create_user", 1)])
        return coll

    @cached_property
    def known_users(self):
        coll = self.db.get_collection("known_users")
        coll.create_index([("name", 1)], unique=True)
        return coll

    @cached_property
    def known_names(self):
        coll = self.db.get_collection("known_names")
        coll.create_index([("name", 1)], unique=True)
        return coll

    @cached_property
    def embedding_models(self):
        coll = self.db.get_collection("embedding_models")
        coll.create_index([("name", 1)], unique=True)
        return coll

    @cached_property
    def locks(self):
        coll = self.db.get_collection("locks")
        coll.create_index([("key", 1)], unique=True)
        return coll

    @cached_property
    def counters(self):
        coll = self.db.get_collection("counters")
        coll.create_index([("key", 1)], unique=True)
        return coll

    @cached_property
    def triggers(self):
        coll = self.db.get_collection("triggers")
        coll.create_index([("id", 1)], unique=True)
        coll.create_index([("name", 1)], unique=True)
        return coll


class LockMismatchError(Exception):
    pass


class ShouldRetryError(Exception):
    pass


class VersionalLocker:
    def __init__(self, db: Database) -> None:
        self.coll = DbCollections(db)

    def read_ahead(self, key: str) -> int:
        """Read the lock version for a given key."""
        lock_data = self.coll.locks.find_one({"key": key})
        return lock_data["version"] if lock_data else 0

    def post_commit(self, key: str, version: int) -> None:
        """Commit the lock version for a given key."""
        if version == 0:
            try:
                self.coll.locks.insert_one({"key": key, "version": 1})
            except pymongo.errors.DuplicateKeyError:
                raise LockMismatchError(f"Lock for {key}::{version} expired.")
        else:
            result = self.coll.locks.update_one(
                {"key": key, "version": version},
                {"$set": {"version": version + 1}},
            )
            if result.modified_count == 0:
                raise LockMismatchError(f"Lock for {key}::{version} expired.")

    def run_with_lock(self, key: str, func: Callable[[], None]):
        """Run a function with a lock on the given key."""
        locked_version = self.read_ahead(key)
        func()
        self.post_commit(key, locked_version)


class DistributedCounters:
    def __init__(self, db: Database) -> None:
        self.coll = DbCollections(db)

    def next(self, key: str) -> int:
        """Get the next value (start from 1) of the counter for the given key."""
        result = self.coll.counters.find_one_and_update(
            {"key": key},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return result["value"]


def _measure_time(func):
    """Decorator to time a function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        doc_store: DocStore | None = None
        if len(args) > 0 and isinstance(args[0], DocStore):
            doc_store = args[0]

        start_time = 0
        if doc_store and doc_store.measure_time:
            start_time = time.time()

        try:
            return func(*args, **kwargs)
        finally:
            if start_time > 0 and doc_store is not None:
                name = func.__name__
                times = doc_store.times
                elapsed = time.time() - start_time
                times[name] = elapsed + times.get(name, 0)

    return wrapper


class Entity(BaseModel):
    pass


class TaggableEntity(Entity):
    tags: list[str]


class DocEntity(TaggableEntity):
    pdf_path: str
    pdf_filename: str | None
    pdf_filesize: int
    pdf_hash: str
    num_pages: int
    page_width: float
    page_height: float
    metadata: dict

    # Original file info (if exists)
    orig_path: str | None
    orig_filename: str | None
    orig_filesize: int | None
    orig_hash: str | None


class PageEntity(TaggableEntity):
    doc_id: str | None
    page_idx: int | None
    image_path: str
    image_filesize: int
    image_hash: str
    image_width: int
    image_height: int
    image_dpi: int | None
    providers: list[str]


class BlockEntity(TaggableEntity):
    layout_id: str | None
    provider: str | None

    page_id: str | None
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270]
    score: float | None

    image_path: str | None
    image_filesize: int | None
    image_hash: str | None
    image_width: int | None
    image_height: int | None

    versions: list[str]


class MaskBlockEntity(Entity):
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270]
    attrs: dict[str, Any]


class LayoutBlockEntity(Entity):
    id: str
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270]


class LayoutContentEntity(Entity):
    id: str
    block_id: str
    format: str
    content: str


class LayoutEntity(TaggableEntity):
    id: str
    page_id: str
    provider: str
    masks: list[MaskBlockEntity]
    blocks: list[LayoutBlockEntity]
    relations: list[dict]
    contents: list[LayoutContentEntity]
    is_human_label: bool


class ContentEntity(TaggableEntity):
    block_id: str
    version: str
    page_id: str | None
    format: str
    content: str
    is_human_label: bool


class ValueEntity(Entity):
    elem_id: str
    key: str
    type: str
    value: Any


class KnownNameEntity(Entity):
    name: str
    display_name: str
    description: str
    type: Literal["tag", "attr", "metric", "project_tag", "dataset_tag", "model_tag"]
    value_type: Literal["null", "int", "float", "str", "list_str", "bool"]
    min_value: float
    max_value: float
    options: dict[str, dict]
    disabled: bool


class EvalLayoutBlockEntity(Entity):
    id: str
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    format: str
    content: str


class EvalLayoutEntity(Entity):
    layout_id: str
    provider: str
    blocks: list[EvalLayoutBlockEntity]
    relations: list[dict]
    status: str


class EvalContentEntity(Entity):
    content_id: str
    version: str
    status: str
    format: str
    content: str


class DocStore(DocStoreInterface):
    def __init__(self, measure_time=False, disable_events=False, decode_value=True):
        self.db_client = get_mongo_client()
        self.db = self.db_client.get_database()
        self.coll = DbCollections(self.db)
        self.counters = DistributedCounters(self.db)
        self.es_client = get_es_client()
        self.redis_stream = RedisStream()
        self.measure_time = measure_time
        self.decode_value = decode_value
        self.max_task_priority = 2
        self.times = {}

        self._event_sink = None
        if not disable_events:
            self._event_sink = KafkaWriter()

        self.username = get_username()
        self.hostname = socket.gethostname()
        self.pid = os.getpid()

        if self.username not in self.all_users:
            warnings.warn(
                f"User [{self.username}] is not a known writer, read-only mode enabled.",
                UserWarning,
            )

    def impersonate(self, username: str) -> "DocStore":
        """Impersonate another user for this DocStore instance."""
        # use __new__ to bypass __init__
        new_store = self.__class__.__new__(self.__class__)
        new_store.db_client = self.db_client
        new_store.db = self.db
        new_store.coll = self.coll
        new_store.counters = self.counters
        new_store.es_client = self.es_client
        new_store.redis_stream = self.redis_stream
        new_store.measure_time = self.measure_time
        new_store.decode_value = self.decode_value
        new_store.max_task_priority = self.max_task_priority
        new_store.times = {}
        new_store._event_sink = self._event_sink
        new_store.username = username
        new_store.hostname = self.hostname
        new_store.pid = self.pid
        return new_store

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.flush()

    def _check_writable(self, check_admin: bool = False) -> None:
        """Check if the current user can write data to the DocStore."""
        user_info = self.user_info
        if not user_info:
            raise PermissionError(f"User [{self.username}] cannot write data to DocStore.")
        if check_admin and not user_info.get("is_admin"):
            raise PermissionError(f"User [{self.username}] is not an admin user.")

    def _check_basic_name(self, name_type: Literal["provider", "version", "key", "tag", "trigger"], name: str) -> None:
        if not isinstance(name, str):
            raise ValueError(f"{name_type} must be a string.")
        if not re.match(r"^[a-zA-Z0-9_]+$", name):
            raise ValueError(f"{name_type} must contain only alphanumeric characters and underscores.")

    def _check_name(self, name_type: Literal["provider", "version", "key", "tag", "trigger"], name: str) -> None:
        """Check if the provider or version is valid."""
        self._check_basic_name(name_type, name)
        aliases = self.user_info.get("aliases") or []
        valid_prefixes = [f"{prefix}__" for prefix in [self.username, *aliases]]
        if any(name.startswith(prefix) for prefix in valid_prefixes):
            return  # Valid prefix
        raise ValueError(f"{name_type.capitalize()} must start with {valid_prefixes}.")

    def _check_tag_name(self, name: str):
        """Check if the tag name is valid for add/del operation."""
        if not isinstance(name, str):
            raise ValueError(f"Tag must be a string.")
        name_info: KnownName | None = self.all_known_names["tag"].get(name)
        if name_info is not None and name_info.disabled:
            raise ValueError(f"Tag name [{name}] is disabled.")
        if name_info is not None and not self.user_info.get("restricted"):
            return  # Known tag, no need to check prefix
        self._check_name("tag", name)  # check if the tag is having a valid prefix

    def _check_and_get_name_info(self, name_type: Literal["attr", "metric"], name: str) -> KnownName:
        if not isinstance(name, str):
            raise ValueError(f"{name_type.capitalize()} name must be a string.")
        name_info: KnownName | None = self.all_known_names[name_type].get(name)
        if name_info is None:
            raise ValueError(f"Unknown {name_type} name [{name}].")
        if name_info.disabled:
            raise ValueError(f"{name_type.capitalize()} [{name}] is disabled.")
        if self.user_info.get("restricted"):
            raise ValueError(f"User [{self.username}] is restricted to write attrs/metrics.")
        return name_info

    def _check_attr_name_and_value(self, name: str, value: Any) -> None:
        name_info = self._check_and_get_name_info("attr", name)
        known_options = set([opt.name for opt in name_info.options])
        if name_info.value_type == "str":
            if not isinstance(value, str):
                raise ValueError(f"Attr {name} requires str value.")
            if value not in known_options:
                raise ValueError(f"Attr {name} has no option {value}.")
        elif name_info.value_type == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"Attr {name} requires bool value.")
        elif name_info.value_type == "int":
            if not isinstance(value, int):
                raise ValueError(f"Attr {name} requires int value.")
            if not (name_info.min_value <= value <= name_info.max_value):
                raise ValueError(f"Attr {name} value {value} out of range [{name_info.min_value}, {name_info.max_value}].")
        elif name_info.value_type == "list_str":
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ValueError(f"Attr {name} requires list of str value.")
            unknown_options = set(value) - known_options
            if unknown_options:
                raise ValueError(f"Attr {name} has no options: {unknown_options}.")

    def _check_metric_name_and_value(self, name: str, value: Any) -> None:
        name_info = self._check_and_get_name_info("metric", name)
        if name_info.value_type == "int" and not isinstance(value, int):
            raise ValueError(f"Metric {name} requires int value.")
        if not (name_info.min_value <= value <= name_info.max_value):
            raise ValueError(f"Metric {name} value {value} out of range [{name_info.min_value}, {name_info.max_value}].")

    def _new_id(self, elem_type: type[E]) -> str:
        """Generate a new unique ID for an element."""
        if elem_type not in (Doc, Page, Layout, Block, Content, Value, Task, EvalLayout, EvalContent):
            raise ValueError(f"Unknown element type {elem_type}.")
        return f"{elem_type.__name__.lower()}-{oid()}"

    def _rand_num(self) -> int:
        """Generate a random number for an element."""
        return random.randint(0, (1 << 31) - 1)

    def _get_type(self, type_name: str):
        type_name = type_name.lower()
        if type_name in ("page", "pages"):
            return Page
        elif type_name in ("layout", "layouts"):
            return Layout
        elif type_name in ("block", "blocks"):
            return Block
        elif type_name in ("content", "contents"):
            return Content
        elif type_name in ("doc", "docs"):
            return Doc
        elif type_name in ("value", "values"):
            return Value
        elif type_name in ("eval_layout", "eval_layouts"):
            return EvalLayout
        elif type_name in ("eval_content", "eval_contents"):
            return EvalContent
        else:
            raise ValueError(f"Unknown element type {type_name}.")

    def _get_coll(self, elem_type: ElemType | type[E]):
        if elem_type == Page or elem_type == "page":
            return self.coll.pages
        elif elem_type == Layout or elem_type == "layout":
            return self.coll.layouts
        elif elem_type == Block or elem_type == "block":
            return self.coll.blocks
        elif elem_type == Content or elem_type == "content":
            return self.coll.contents
        elif elem_type == Doc or elem_type == "doc":
            return self.coll.docs
        elif elem_type == Value or elem_type == "value":
            return self.coll.values
        elif elem_type == EvalLayout or elem_type == "eval_layout":
            return self.coll.eval_layouts
        elif elem_type == EvalContent or elem_type == "eval_content":
            return self.coll.eval_contents
        else:
            raise ValueError(f"Unknown element type {elem_type}.")

    def _get_elem_type_by_id(self, elem_id: str):
        if elem_id.startswith("page-"):
            return Page
        elif elem_id.startswith("layout-"):
            if ".block-" in elem_id:
                return Block
            if ".content-" in elem_id:
                return Content
            return Layout
        elif elem_id.startswith("block-"):
            return Block
        elif elem_id.startswith("content-"):
            return Content
        elif elem_id.startswith("doc-"):
            return Doc
        elif elem_id.startswith("value-"):
            return Value
        elif elem_id.startswith("evallayout-"):
            return EvalLayout
        elif elem_id.startswith("evalcontent-"):
            return EvalContent
        # fallback to block
        return Block

    @_measure_time
    def _dump_elem(self, entity: Entity) -> dict:
        """Pre-process element data before insertion."""
        if isinstance(entity, BlockEntity):
            x1, y1, x2, y2 = entity.bbox
            return {
                "layout_id": entity.layout_id,
                "provider": entity.provider,
                "page_id": entity.page_id,
                "type": entity.type,
                "bbox": f"{x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f}",
                "angle": entity.angle,
                "score": entity.score,
                "image_path": entity.image_path,
                "image_filesize": entity.image_filesize,
                "image_hash": entity.image_hash,
                "image_width": entity.image_width,
                "image_height": entity.image_height,
                "tags": entity.tags,
            }
        if isinstance(entity, LayoutBlockEntity):
            x1, y1, x2, y2 = entity.bbox
            return {
                "id": entity.id,
                "type": entity.type,
                "bbox": f"{x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f}",
                "angle": entity.angle,
            }
        if isinstance(entity, MaskBlockEntity):
            x1, y1, x2, y2 = entity.bbox
            return {
                "type": entity.type,
                "bbox": f"{x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f}",
                "angle": entity.angle,
                "attrs": entity.attrs,
            }
        if isinstance(entity, LayoutEntity):
            return {
                "id": entity.id,
                "page_id": entity.page_id,
                "provider": entity.provider,
                "masks": [self._dump_elem(m) for m in entity.masks],
                "blocks": [self._dump_elem(b) for b in entity.blocks],
                "relations": entity.relations,
                "contents": [self._dump_elem(c) for c in entity.contents],
                "is_human_label": entity.is_human_label,
                "tags": entity.tags,
            }
        if isinstance(entity, EvalLayoutEntity):
            return {
                "layout_id": entity.layout_id,
                "provider": entity.provider,
                "blocks": [self._dump_elem(b) for b in entity.blocks],
                "relations": entity.relations,
                "status": entity.status,
            }
        if isinstance(entity, EvalContentEntity):
            return {
                "content_id": entity.content_id,
                "version": entity.version,
                "format": entity.format,
                "content": entity.content,
                "status": entity.status,
            }
        return entity.model_dump()

    def _parse_block(self, block_data: dict) -> dict:
        """Parse bbox in block data."""
        if "angle" not in block_data:
            block_data["angle"] = None

        bbox = block_data.get("bbox")

        # TODO: temp code
        if not bbox:
            block_data["bbox"] = [0.0, 0.0, 1.0, 1.0]
            block_data["type"] = "super"
            return block_data

        if isinstance(bbox, str):
            block_data["bbox"] = list(map(float, bbox.split(",")))
            return block_data
        if isinstance(bbox, (list, tuple)):
            return block_data
        raise ValueError("bbox must be a string or a list of floats.")

    @_measure_time
    def _parse_elem(self, elem_type: type[E], elem_data: dict) -> E:
        """Post-process element data after retrieval or insertion."""
        _id: ObjectId | None = elem_data.pop("_id", None)  # Hide MongoDB's _id

        if "create_time" not in elem_data and _id is not None:
            elem_data["create_time"] = int(_id.generation_time.timestamp() * 1000)
        if "update_time" not in elem_data and elem_data.get("create_time"):
            elem_data["update_time"] = elem_data["create_time"]

        if elem_data.get("rid") is None:
            elem_data["rid"] = 0
        if elem_data.get("tags") is None:
            elem_data["tags"] = []
        if elem_data.get("attrs") is None:
            elem_data["attrs"] = {}
        if elem_data.get("metrics") is None:
            elem_data["metrics"] = {}

        if elem_type == Block:
            elem_data = self._parse_block(elem_data)
        elif elem_type == Layout:
            page_id = elem_data.get("page_id") or ""
            masks = elem_data.get("masks") or []
            blocks = elem_data.get("blocks") or []
            contents = elem_data.get("contents") or []
            for block_data in blocks:
                block_data["page_id"] = page_id
                block_data["create_time"] = elem_data.get("create_time")
            for content_data in contents:
                content_data["page_id"] = page_id
                content_data["version"] = elem_data.get("provider")
                content_data["is_human_label"] = elem_data.get("is_human_label", False)
                content_data["create_time"] = elem_data.get("create_time")
            elem_data["masks"] = [MaskBlock(**self._parse_block(m)) for m in masks]
            elem_data["blocks"] = [self._parse_elem(Block, b) for b in blocks]
            elem_data["contents"] = [self._parse_elem(Content, c) for c in contents]
        elif elem_type == EvalLayout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [EvalLayoutBlock(**b) if isinstance(b, dict) else b for b in blocks]
            elem_data["status"] = EvalStatus(elem_data.get("status", EvalStatus.PENDING))
        elif elem_type == EvalContent:
            elem_data["status"] = EvalStatus(elem_data.get("status", EvalStatus.PENDING))
        elif elem_type == Content:
            elem_data["format"] = elem_data.get("format", "text")

        elem_object = elem_type(**elem_data)
        elem_object.store = self

        if isinstance(elem_object, Value) and self.decode_value:
            elem_object.decode()
        return elem_object

    def _parse_known_name(self, name_data: dict) -> KnownName:
        """Parse known name data after retrieval."""
        options_dict = name_data.get("options") or {}
        options_list = [{"name": k, **v} for k, v in options_dict.items()]
        name_data = {k: v for k, v in name_data.items() if k not in ("_id", "options")}
        name_data["options"] = options_list
        return KnownName(**name_data)

    @_measure_time
    def _try_get_elem(self, elem_type: type[E], query: dict) -> E | None:
        """Try to get an element by its type and query, return None if not found."""
        coll = self._get_coll(elem_type)
        elem_data = coll.find_one(query)
        if elem_data is None:
            return None
        return self._parse_elem(elem_type, elem_data)

    @_measure_time
    def _get_elem(self, elem_type: type[E], query: dict) -> E:
        """Get an element by its type and query, raise ValueError if not found."""
        elem_data = self._try_get_elem(elem_type, query)
        if elem_data is None:
            raise ElementNotFoundError(f"{elem_type.__name__} with {query} not found.")
        return elem_data

    def _write_event(
        self,
        elem_type: Literal["doc", "page", "layout", "block", "content"] | str | type,
        event_type: Literal["insert", "add_tag", "del_tag", "add_provider", "add_version"],
        elem_data: dict | None,
        tag_added: str | None = None,
        tag_deleted: str | None = None,
        provider_added: str | None = None,
        version_added: str | None = None,
    ) -> None:
        if self._event_sink is None:
            return
        if isinstance(elem_type, type):
            elem_type = elem_type.__name__.lower()
        if elem_type not in ("doc", "page", "layout", "block", "content"):
            return
        if elem_data is None:
            return
        event_data = DocEvent(
            elem_id=elem_data["id"],
            elem_type=elem_type,
            event_type=event_type,
            event_user=self.username,
            page_providers=elem_data.get("providers") if elem_type == "page" else None,
            layout_provider=elem_data.get("provider") if elem_type == "layout" else None,
            block_type=elem_data.get("type") if elem_type == "block" else None,
            block_versions=elem_data.get("versions") if elem_type == "block" else None,
            content_version=elem_data.get("version") if elem_type == "content" else None,
            tags=elem_data.get("tags"),
            tag_added=tag_added,
            tag_deleted=tag_deleted,
            provider_added=provider_added,
            version_added=version_added,
        )
        event_data_dict = event_data.model_dump()
        event_data_dict = {k: v for k, v in event_data_dict.items() if v is not None}
        self._event_sink.write(event_data_dict)

    @_measure_time
    def _insert_elem(self, elem_type: type[E], entity: Entity, parent_id: str | None = None) -> E | None:
        """Insert a new element into the database."""
        self._check_writable()

        if not isinstance(entity, Entity):
            raise ValueError(f"entity must be an instance of Entity, not {type(entity)}.")

        if isinstance(entity, TaggableEntity):
            for tag in entity.tags:
                self._check_tag_name(tag)

        coll = self._get_coll(elem_type)

        now = int(time.time() * 1000)
        elem_data = self._dump_elem(entity)

        if not elem_data.get("id"):
            elem_id = self._new_id(elem_type)
            if parent_id is not None:
                elem_id = f"{parent_id}.{elem_id}"
            elem_data["id"] = elem_id

        elem_data["rid"] = self._rand_num()
        elem_data["create_time"] = now
        elem_data["update_time"] = now

        try:
            coll.insert_one(elem_data)
        except pymongo.errors.DuplicateKeyError:
            return None

        self._write_event(elem_type, "insert", elem_data)

        # remove in future.
        if isinstance(entity, TaggableEntity):
            for tag in elem_data.get("tags") or []:
                self.add_tag(elem_data["id"], tag)

        return self._parse_elem(elem_type, elem_data)

    @_measure_time
    def _upsert_elem(self, elem_type: type[E], query: dict, entity: Entity, parent_id: str | None = None) -> E:
        """Upsert an element into the database."""
        self._check_writable()

        if elem_type not in (Layout, Content):
            raise ValueError(f"Only Layout and Content can be upsert, not {elem_type.__name__}.")
        if not isinstance(query, dict) or not query:
            raise ValueError("query must be a non-empty dictionary.")
        if not isinstance(entity, Entity):
            raise ValueError(f"entity must be an instance of Entity, not {type(entity)}.")

        elem_data = self._dump_elem(entity)
        for key, val in query.items():
            if key in elem_data and elem_data.pop(key) != val:
                raise ValueError(f"Query key '{key}' value '{val}' does not match with update data.")

        if isinstance(entity, TaggableEntity):
            for tag in entity.tags:
                self._check_tag_name(tag)

        coll = self._get_coll(elem_type)

        now = int(time.time() * 1000)
        elem_data["update_time"] = now

        insert_data = {**query}

        if not elem_data.get("id"):
            elem_id = self._new_id(elem_type)
            if parent_id is not None:
                elem_id = f"{parent_id}.{elem_id}"
            insert_data["id"] = elem_id

        insert_data["rid"] = self._rand_num()
        insert_data["create_time"] = now

        result_data = coll.find_one_and_update(
            query,
            {"$set": elem_data, "$setOnInsert": insert_data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        self._write_event(elem_type, "insert", result_data)

        # remove in future.
        if isinstance(entity, TaggableEntity):
            for tag in elem_data.get("tags") or []:
                self.add_tag(result_data["id"], tag)

        return self._parse_elem(elem_type, result_data)

    def _check_blocks(self, blocks: Sequence[BlockInput]) -> None:
        for block in blocks:
            if not isinstance(block, BlockInput):
                raise ValueError("Each block must be a BlockInput instance.")

            bbox = block.bbox
            if len(bbox) != 4:
                raise ValueError("bbox must contain exactly 4 float values.")
            if not all(isinstance(x, (int, float)) for x in bbox):
                raise ValueError("bbox values must be integers or floats.")
            if any(not (0.0 <= x <= 1.0) for x in bbox):
                raise ValueError("bbox values must be in the range [0.0, 1.0].")
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise ValueError("bbox values are invalid: x1 >= x2 or y1 >= y2.")

            block_type = block.type
            if not block_type:
                raise ValueError("block type cannot be empty.")
            if block_type not in BLOCK_TYPES:
                raise ValueError(f"unknown block type: {block_type}.")

            block_angle = block.angle
            if block_angle not in ANGLE_OPTIONS:
                raise ValueError(f"Invalid angle: {block_angle}. Must be one of {ANGLE_OPTIONS}.")

            if block_type == "super":
                if bbox != [0.0, 0.0, 1.0, 1.0]:
                    raise ValueError("Super block must have bbox [0.0, 0.0, 1.0, 1.0].")
                if block_angle is not None:
                    raise ValueError("Super block cannot have angle.")

    def _check_mask_blocks(self, blocks: Sequence[MaskBlock]) -> None:
        for block in blocks:
            if not isinstance(block, MaskBlock):
                raise ValueError("Each block must be a MaskBlock instance.")

            bbox = block.bbox
            if len(bbox) != 4:
                raise ValueError("bbox must contain exactly 4 float values.")
            if not all(isinstance(x, (int, float)) for x in bbox):
                raise ValueError("bbox values must be integers or floats.")
            if any(not (0.0 <= x <= 1.0) for x in bbox):
                raise ValueError("bbox values must be in the range [0.0, 1.0].")
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise ValueError("bbox values are invalid: x1 >= x2 or y1 >= y2.")

            mask_type = block.type
            if not mask_type:
                raise ValueError("block type cannot be empty.")
            if mask_type not in BLOCK_TYPES:
                raise ValueError(f"unknown block type: {mask_type}.")

            block_angle = block.angle
            if block_angle not in ANGLE_OPTIONS:
                raise ValueError(f"Invalid angle: {block_angle}. Must be one of {ANGLE_OPTIONS}.")

            for attr_name, attr_value in (block.attrs or {}).items():
                self._check_attr_name_and_value(attr_name, attr_value)

    @_measure_time
    def _insert_blocks(
        self,
        page_id: str,
        blocks: Sequence[BlockInput],
        layout_id: str | None = None,
        provider: str | None = None,
    ) -> list[Block]:
        """Insert blocks for a page, return list of inserted blocks."""
        self._check_writable()
        if not blocks:
            return []
        self._check_blocks(blocks)

        result_blocks: list[Block] = []
        for block_input in blocks:
            block_entity = BlockEntity(
                layout_id=layout_id,
                provider=provider,
                page_id=page_id,
                type=block_input.type,
                bbox=block_input.bbox,
                angle=block_input.angle,
                score=block_input.score,
                image_path=None,
                image_filesize=None,
                image_hash=None,
                image_width=None,
                image_height=None,
                versions=[],
                tags=block_input.tags or [],
            )
            block = self._insert_elem(Block, block_entity, parent_id=layout_id)
            assert block is not None
            result_blocks.append(block)

        return result_blocks

    @_measure_time
    def _insert_content(
        self,
        block_id: str,
        version: str,
        content_input: ContentInput,
        layout_id: str,
        page_id: str,
        upsert=False,
    ) -> Content:
        """Insert a new content for a block (block is already inserted)."""
        self._check_writable()
        self._check_name("version", version)

        if not block_id:
            raise ValueError("block_id must be provided.")
        if not isinstance(content_input, ContentInput):
            raise ValueError("content_input must be a ContentInput instance.")

        format = content_input.format
        if not format:
            raise ValueError("content_input must contain 'format'.")
        if format not in CONTENT_FORMATS:
            raise ValueError(f"unknown content format: {format}.")

        content_entity = ContentEntity(
            block_id=block_id,
            version=version,
            page_id=page_id,
            format=format,
            content=content_input.content,
            is_human_label=content_input.is_human_label,
            tags=content_input.tags or [],
        )

        if upsert:
            # TODO: upsert may cause difference to layout.content
            query = {"block_id": block_id, "version": version}
            result = self._upsert_elem(Content, query, content_entity, parent_id=layout_id)
        else:  # insert
            result = self._insert_elem(Content, content_entity, parent_id=layout_id)
            if result is None:
                raise ElementExistsError(
                    f"Content for block {block_id} with version {version} already exists.",
                )

        # add version to block.versions
        self._get_coll(Block).update_one(
            {"id": block_id},
            {"$addToSet": {"versions": version}},
        )

        return result

    def _normalize_unstored_blocks(self, page_id: str, blocks: Sequence[BlockInput], layout_id: str) -> list[Block]:
        """Normalize unstored blocks by ensuring they have IDs and valid bbox."""
        self._check_blocks(blocks)

        if any(block_input.tags for block_input in blocks):
            raise ValueError(f"Unstored block should not have tags.")

        result_blocks: list[Block] = []
        for block_input in blocks:
            block = Block(
                id=f"{layout_id}.{self._new_id(Block)}",
                rid=0,
                page_id=page_id,
                type=block_input.type,
                bbox=[round(num, 4) for num in block_input.bbox],
                angle=block_input.angle,
                tags=block_input.tags or [],
            )
            result_blocks.append(block)

        return result_blocks

    def _normalize_unstored_content(self, block: Block, version: str, content_input: ContentInput, layout_id: str) -> Content:
        """Normalize unstored content by ensuring it has valid fields."""

        if not block:
            raise ValueError("block must be provided.")
        if not isinstance(content_input, ContentInput):
            raise ValueError("content_input must be a ContentInput instance.")

        format = content_input.format
        if not format:
            raise ValueError("content_input must contain 'format'.")
        if format not in CONTENT_FORMATS:
            raise ValueError(f"unknown content format: {format}.")

        content = Content(
            id=f"{layout_id}.{self._new_id(Content)}",
            rid=0,
            block_id=block.id,
            version=version,
            page_id=block.page_id,
            format=format,
            content=content_input.content,
            is_human_label=content_input.is_human_label,
            tags=content_input.tags or [],
        )
        return content

    #########################
    # MANAGEMENT OPERATIONS #
    #########################

    @property
    def user_info(self) -> User | dict:
        return self.all_users.get(self.username) or {}

    @timed_property(ttl=10)
    def all_users(self) -> dict[str, User]:
        return {user.name: user for user in self.list_users()}

    @timed_property(ttl=10)
    def all_known_names(self) -> dict[str, dict[str, KnownName]]:
        all_names: dict[str, dict[str, KnownName]] = {}
        all_names["tag"], all_names["attr"], all_names["metric"] = {}, {}, {}
        for known_name in self.list_known_names():
            all_names.setdefault(known_name.type, {})[known_name.name] = known_name
        return all_names

    def list_users(self) -> list[User]:
        """List all users in the system."""
        users: list[User] = []
        for user_data in self.coll.known_users.find({}):
            user_data.pop("_id", None)
            try:
                users.append(User(**user_data))
            except Exception as e:
                warnings.warn(f"Failed to parse user data {user_data}: {e}")
        return users

    def get_user(self, name: str) -> User:
        """Get a user by name."""
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        user_data = self.coll.known_users.find_one({"name": name})
        if user_data is None:
            raise NotFoundError(f"User [{name}] does not exist.")
        user_data.pop("_id", None)
        return User(**user_data)

    def insert_user(self, user_input: UserInput) -> User:
        """Add a new user to the system."""
        self._check_writable(check_admin=True)
        if not isinstance(user_input, UserInput):
            raise ValueError("user_input must be an instance of UserInput.")
        if not user_input.name:
            raise ValueError("User name cannot be empty.")
        if self.coll.known_users.find_one({"name": user_input.name}):
            raise AlreadyExistsError(f"User [{user_input.name}] already exists.")
        try:
            user_data = user_input.model_dump()
            self.coll.known_users.insert_one(user_data)
        except pymongo.errors.DuplicateKeyError:
            raise AlreadyExistsError(f"User [{user_input.name}] already exists.")
        user_data.pop("_id", None)
        return User(**user_data)

    def update_user(self, name: str, user_update: UserUpdate) -> User:
        """Update an existing user in the system."""
        self._check_writable(check_admin=True)
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        if not isinstance(user_update, UserUpdate):
            raise ValueError("user_update must be an instance of UserUpdate.")

        user_update_data = user_update.model_dump()
        user_update_data = {k: v for k, v in user_update_data.items() if v is not None}

        if user_update_data:
            user_data = self.coll.known_users.find_one_and_update(
                {"name": name},
                {"$set": user_update_data},
                upsert=False,
                return_document=ReturnDocument.AFTER,
            )
        else:  # nothing to update
            user_data = self.coll.known_users.find_one({"name": name})

        if user_data is None:
            raise NotFoundError(f"Known name [{name}] does not exist.")

        user_data.pop("_id", None)
        return User(**user_data)

    def list_known_names(self) -> list[KnownName]:
        """List all known tag/attribute/metric names in the system."""
        known_names: list[KnownName] = []
        for data in self.coll.known_names.find({}):
            known_names.append(self._parse_known_name(data))
        return known_names

    def insert_known_name(self, known_name_input: KnownNameInput) -> KnownName:
        """Add a new known tag/attribute/metric name to the system."""
        self._check_writable(check_admin=True)
        if not isinstance(known_name_input, KnownNameInput):
            raise ValueError("known_name_input must be an instance of KnownNameInput.")

        name_pattern = r"^[a-zA-Z0-9_]+$"
        if known_name_input.type in ("attr", "metric"):
            # attr and metric names can have hyphens
            name_pattern = r"^[a-zA-Z0-9_-]+$"
        if not re.match(name_pattern, known_name_input.name):
            raise ValueError(f"Name must contain only alphanumeric characters and underscores.")

        if known_name_input.type == "tag":
            if known_name_input.value_type != "null":
                raise ValueError(f"Tag type must have value_type 'null'.")
            if "__" not in known_name_input.name:
                raise ValueError(f"Tag name must contain '__' to separate prefix.")
        elif known_name_input.type == "attr":
            if known_name_input.value_type not in ("str", "list_str", "int", "bool"):
                raise ValueError(f"Attr type must have value_type 'str', 'list_str', 'int', or 'bool'.")
        elif known_name_input.type == "metric":
            if known_name_input.value_type not in ("int", "float"):
                raise ValueError(f"Metric type must have value_type 'int' or 'float'.")
        else:  # other tags that are not used by doc store.
            if known_name_input.value_type != "null":
                raise ValueError(f"Tag type must have value_type 'null'.")

        if self.coll.known_names.find_one({"name": known_name_input.name}):
            raise AlreadyExistsError(f"Name [{known_name_input.name}] already exists.")

        name_entity = KnownNameEntity(
            name=known_name_input.name,
            display_name=known_name_input.display_name,
            description=known_name_input.description,
            type=known_name_input.type,
            value_type=known_name_input.value_type,
            min_value=known_name_input.min_value,
            max_value=known_name_input.max_value,
            options={},
            disabled=False,
        )

        try:
            name_data = name_entity.model_dump()
            self.coll.known_names.insert_one(name_data)
        except pymongo.errors.DuplicateKeyError:
            raise AlreadyExistsError(f"Name [{known_name_input.name}] already exists.")

        return self._parse_known_name(name_data)

    def update_known_name(self, name: str, known_name_update: KnownNameUpdate) -> KnownName:
        """Update an existing known tag/attribute/metric name in the system."""
        self._check_writable(check_admin=True)
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        if not isinstance(known_name_update, KnownNameUpdate):
            raise ValueError("known_name_update must be an instance of KnownNameUpdate.")

        name_update = known_name_update.model_dump()
        name_update = {k: v for k, v in name_update.items() if v is not None}

        if name_update:
            name_data = self.coll.known_names.find_one_and_update(
                {"name": name},
                {"$set": name_update},
                upsert=False,
                return_document=ReturnDocument.AFTER,
            )
        else:  # nothing to update
            name_data = self.coll.known_names.find_one({"name": name})

        if name_data is None:
            raise NotFoundError(f"Known name [{name}] does not exist.")

        return self._parse_known_name(name_data)

    def add_known_option(self, attr_name: str, option_name: str, option_input: KnownOptionInput) -> None:
        """Add/Update a new known option to a known attribute name."""
        self._check_writable(check_admin=True)
        if not isinstance(attr_name, str) or not attr_name:
            raise ValueError("attr_name must be a non-empty string.")
        if not isinstance(option_name, str) or not option_name:
            raise ValueError("option_name must be a non-empty string.")
        if not isinstance(option_input, KnownOptionInput):
            raise ValueError("option_input must be an instance of KnownOptionInput.")
        if not re.match(r"^[a-zA-Z0-9_]+$", option_name):
            raise ValueError(f"Option name must contain only alphanumeric characters and underscores.")

        name_data = self.coll.known_names.find_one({"name": attr_name})
        if name_data is None:
            raise NotFoundError(f"Attr name [{attr_name}] does not exist.")

        option_data = {
            "display_name": option_input.display_name,
            "description": option_input.description,
        }

        if not self.coll.known_names.update_one(
            {"name": attr_name, "options": None},
            {"$set": {"options": {option_name: option_data}}},
        ).modified_count:
            self.coll.known_names.update_one(
                {"name": attr_name},
                {"$set": {f"options.{option_name}": option_data}},
            )

    def del_known_option(self, attr_name: str, option_name: str) -> None:
        """Delete a known option from a known attribute name."""
        self._check_writable(check_admin=True)
        if not isinstance(attr_name, str) or not attr_name:
            raise ValueError("attr_name must be a non-empty string.")
        if not isinstance(option_name, str) or not option_name:
            raise ValueError("option_name must be a non-empty string.")
        self.coll.known_names.update_one(
            {"name": attr_name},
            {"$unset": {f"options.{option_name}": ""}},
        )

    ###################
    # READ OPERATIONS #
    ###################

    def health_check(self, show_stats: bool = False) -> dict:
        """Check the health of the doc store."""
        server_info = {
            "healthy": True,
            "version": doc_store_version,
            "min_required_version": min_required_version,
            "hostname": self.hostname,
            "pid": self.pid,
        }
        if show_stats:
            server_info["db_stats"] = pool_stats(self.db_client)
        return server_info

    @_measure_time
    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        return self._get_elem(Doc, {"id": doc_id})

    @_measure_time
    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        return self._get_elem(Doc, {"pdf_path": pdf_path})

    @_measure_time
    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        return self._get_elem(Doc, {"pdf_hash": pdf_hash.lower()})

    @_measure_time
    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        return self._get_elem(Page, {"id": page_id})

    @_measure_time
    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        return self._get_elem(Page, {"image_path": image_path})

    @_measure_time
    def get_layout(self, layout_id: str, expand: bool = False) -> Layout:
        """Get a layout by its ID."""
        layout = self._get_elem(Layout, {"id": layout_id})
        return layout.expand() if expand else layout

    @_measure_time
    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str, expand: bool = False) -> Layout:
        """Get a layout by its page ID and provider."""
        layout = self._get_elem(Layout, {"page_id": page_id, "provider": provider})
        return layout.expand() if expand else layout

    @_measure_time
    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        # TODO: fallback to block inside layout
        return self._get_elem(Block, {"id": block_id})

    @_measure_time
    def get_block_by_image_path(self, image_path: str) -> Block:
        """Get a block by its image path."""
        return self._get_elem(Block, {"image_path": image_path})

    @_measure_time
    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        # TODO: temp code
        super_block = self._try_get_elem(Block, {"page_id": page_id, "type": ""})
        if super_block is not None:
            return super_block
        # new code
        super_block = self._try_get_elem(Block, {"page_id": page_id, "type": "super"})
        if super_block is not None:
            return super_block

        if not self.try_get_page(page_id):
            raise ElementNotFoundError(f"Page with ID {page_id} does not exist.")

        return self.insert_block(page_id, BlockInput(type="super", bbox=[0.0, 0.0, 1.0, 1.0]))

    @_measure_time
    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        # TODO: fallback to content inside layout
        return self._get_elem(Content, {"id": content_id})

    @_measure_time
    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        # TODO: fallback to content inside layout
        return self._get_elem(Content, {"block_id": block_id, "version": version})

    @_measure_time
    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        return self._get_elem(Value, {"id": value_id})

    @_measure_time
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its element ID and key."""
        return self._get_elem(Value, {"elem_id": elem_id, "key": key})

    @_measure_time
    def get_eval_layout(self, eval_layout_id: str) -> EvalLayout:
        """Get an eval layout by its ID."""
        return self._get_elem(EvalLayout, {"id": eval_layout_id})

    @_measure_time
    def get_eval_content(self, eval_content_id: str) -> EvalContent:
        """Get an eval content by its ID."""
        return self._get_elem(EvalContent, {"id": eval_content_id})

    @_measure_time
    def distinct_values(
        self,
        elem_type: ElemType | type[T],
        field: Literal["tags", "providers", "provider", "versions", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get distinct values of a field for a given element type."""
        coll = self._get_coll(elem_type)
        return [v for v in coll.distinct(field, query) if v]

    def find(
        self,
        elem_type: ElemType | type[T],
        query: dict | list[dict] | None = None,
        query_from: ElemType | type[Q] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[T]:
        query = query or {}
        query_type = query_from or elem_type

        is_pipeline = isinstance(query, list)
        if query_type != elem_type and not is_pipeline:
            raise ValueError("query_from can only be used in pipeline query.")

        if is_pipeline:
            pipeline = [*query]
            if len(pipeline) > 0 and pipeline[0].get("$from"):
                query_type = self._get_type(pipeline[0]["$from"])
                pipeline = pipeline[1:]
            if skip is not None:
                pipeline.append({"$skip": skip})
            if limit is not None:
                pipeline.append({"$limit": limit})
            coll = self._get_coll(query_type)
            cursor = coll.aggregate(pipeline, maxTimeMS=86400000, batchSize=1000)
        else:  # normal query
            coll = self._get_coll(query_type)
            cursor = coll.find(query, max_time_ms=86400000, batch_size=1000)
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)

        parse_type = elem_type
        if isinstance(elem_type, str):
            parse_type = self._get_type(elem_type)
        for elem_data in cursor:
            yield self._parse_elem(parse_type, elem_data)  # type: ignore

    @_measure_time
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        query = query or {}
        query_type = query_from or elem_type

        is_pipeline = isinstance(query, list)
        if query_type != elem_type and not is_pipeline:
            raise ValueError("query_from can only be used in pipeline query.")

        if estimated and not query:
            coll = self._get_coll(query_type)
            return coll.estimated_document_count()

        if not is_pipeline:
            coll = self._get_coll(query_type)
            return coll.count_documents(query)

        pipeline = [*query]
        if len(pipeline) > 0 and pipeline[0].get("$from"):
            query_type = self._get_type(pipeline[0]["$from"])
            pipeline = pipeline[1:]
        pipeline.append({"$group": {"_id": 1, "n": {"$sum": 1}}})

        coll = self._get_coll(query_type)
        return int(next(coll.aggregate(pipeline))["n"])

    ####################
    # WRITE OPERATIONS #
    ####################

    @_measure_time
    def add_tag(self, elem_id: str, tag: str) -> None:
        # TODO: ensure elem is inserted
        """Add tag to an element."""
        self._check_writable()
        self._check_tag_name(tag)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        elem_data = coll.find_one_and_update(
            filter={"id": elem_id},
            update={"$addToSet": {"tags": tag}, "$set": {"update_time": now}},
            projection=EVENT_PROJECTION,
        )
        self._write_event(elem_type, "add_tag", elem_data, tag_added=tag)

    @_measure_time
    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_tag_name(tag)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        elem_data = coll.find_one_and_update(
            filter={"id": elem_id},
            update={"$pull": {"tags": tag}, "$set": {"update_time": now}},
            projection=EVENT_PROJECTION,
        )
        self._write_event(elem_type, "del_tag", elem_data, tag_deleted=tag)

    def batch_add_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch add tag to multiple elements."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_tag_name(tag)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        for elem_id in elem_ids:
            elem_data = coll.find_one_and_update(
                filter={"id": elem_id},
                update={"$addToSet": {"tags": tag}, "$set": {"update_time": now}},
                projection=EVENT_PROJECTION,
            )
            self._write_event(elem_type, "add_tag", elem_data, tag_added=tag)

    def batch_del_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch delete tag from multiple elements."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_tag_name(tag)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        for elem_id in elem_ids:
            elem_data = coll.find_one_and_update(
                filter={"id": elem_id},
                update={"$pull": {"tags": tag}, "$set": {"update_time": now}},
                projection=EVENT_PROJECTION,
            )
            self._write_event(elem_type, "del_tag", elem_data, tag_deleted=tag)

    @_measure_time
    def add_attr(self, elem_id: str, name: str, attr_input: AttrInput) -> None:
        """Add an attribute to an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        if not isinstance(attr_input, AttrInput):
            raise ValueError("attr_input must be a AttrInput instance.")

        value = attr_input.value
        self._check_attr_name_and_value(name, value)

        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        update_attrs = {
            "attrs": {"$mergeObjects": [{"$ifNull": ["$attrs", {}]}, {name: value}]},
        }
        coll.update_one(
            filter={"id": elem_id},
            update=[{"$set": {**update_attrs, "update_time": now}}],
        )

    @_measure_time
    def add_attrs(self, elem_id: str, attrs: dict[str, AttrValueType]) -> None:
        """Add multiple attributes to an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        for name, value in attrs.items():
            self._check_attr_name_and_value(name, value)

        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        update_attrs = {
            "attrs": {"$mergeObjects": [{"$ifNull": ["$attrs", {}]}, attrs]},
        }
        coll.update_one(
            filter={"id": elem_id},
            update=[{"$set": {**update_attrs, "update_time": now}}],
        )

    @_measure_time
    def del_attr(self, elem_id: str, name: str) -> None:
        """Delete an attribute from an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_and_get_name_info("attr", name)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        coll.update_one(
            {"id": elem_id},
            {
                "$unset": {f"attrs.{name}": ""},
                "$set": {"update_time": now},
            },
        )

    @_measure_time
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        if not isinstance(metric_input, MetricInput):
            raise ValueError("metric_input must be a MetricInput instance.")

        value = metric_input.value
        self._check_metric_name_and_value(name, value)

        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        update_metrics = {
            "metrics": {"$mergeObjects": [{"$ifNull": ["$metrics", {}]}, {name: value}]},
        }
        coll.update_one(
            filter={"id": elem_id},
            update=[{"$set": {**update_metrics, "update_time": now}}],
        )

    @_measure_time
    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_and_get_name_info("metric", name)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        coll.update_one(
            {"id": elem_id},
            {
                "$unset": {f"metrics.{name}": ""},
                "$set": {"update_time": now},
            },
        )

    def tagging(self, elem_id: str, tagging_input: TaggingInput) -> None:
        """Add/Delete tags, attributes, and metrics to/from an element."""
        self._check_writable()

        del_tags = tagging_input.del_tags or []
        del_attrs = tagging_input.del_attrs or []
        del_metrics = tagging_input.del_metrics or []
        tags = [tag for tag in (tagging_input.tags or []) if tag not in del_tags]
        attrs = {k: v for k, v in (tagging_input.attrs or {}).items() if k not in del_attrs}
        metrics = {k: v for k, v in (tagging_input.metrics or {}).items() if k not in del_metrics}

        if not (tags or attrs or metrics or del_tags or del_attrs or del_metrics):
            return  # nothing to do

        for tag in tags + del_tags:
            self._check_tag_name(tag)
        for name, value in attrs.items():
            self._check_attr_name_and_value(name, value)
        for name, value in metrics.items():
            self._check_metric_name_and_value(name, value)
        for name in del_attrs:
            self._check_and_get_name_info("attr", name)
        for name in del_metrics:
            self._check_and_get_name_info("metric", name)

        add_to_set_expr = {"tags": {"$each": tags}} if len(tags) > 1 else {"tags": tags[0]} if tags else {}
        pull_expr = {"tags": {"$in": del_tags}} if len(del_tags) > 1 else {"tags": del_tags[0]} if del_tags else {}
        set_expr = {
            **{f"attrs.{name}": value for name, value in attrs.items()},
            **{f"metrics.{name}": value for name, value in metrics.items()},
            # **({"attrs": {"$mergeObjects": [{"$ifNull": ["$attrs", {}]}, attrs]}} if attrs else {}),
            # **({"metrics": {"$mergeObjects": [{"$ifNull": ["$metrics", {}]}, metrics]}} if metrics else {}),
            "update_time": int(time.time() * 1000),
        }
        unset_expr = {
            **{f"attrs.{name}": "" for name in del_attrs},
            **{f"metrics.{name}": "" for name in del_metrics},
        }
        update1 = {
            **({"$addToSet": add_to_set_expr} if add_to_set_expr else {}),
            **({"$pull": pull_expr} if pull_expr and not add_to_set_expr else {}),
            **({"$set": set_expr} if set_expr else {}),
            **({"$unset": unset_expr} if unset_expr else {}),
        }
        update2 = {
            **({"$pull": pull_expr} if pull_expr and add_to_set_expr else {}),
        }

        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)

        if tagging_input.tags or tagging_input.del_tags:
            elem_data = coll.find_one_and_update(
                filter={"id": elem_id},
                update=update1,
                projection=EVENT_PROJECTION,
            )
        else:  # no tags changed, no need to fetch elem_data
            coll.update_one(filter={"id": elem_id}, update=update1)
            elem_data = None

        if update2:  # need to do pull separately to avoid conflict with addToSet
            coll.update_one(filter={"id": elem_id}, update=update2)

        for tag in tagging_input.tags or []:
            self._write_event(elem_type, "add_tag", elem_data, tag_added=tag)
        for tag in tagging_input.del_tags or []:
            self._write_event(elem_type, "del_tag", elem_data, tag_deleted=tag)

    def batch_tagging(self, elem_type: ElemType, inputs: list[ElementTagging]) -> None:
        """Batch add/delete tags, attributes, and metrics to/from multiple elements."""
        raise NotImplementedError()

    @_measure_time
    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        self._check_writable()
        if not isinstance(doc_input, DocInput):
            raise ValueError("doc_input must be a DocInput instance.")

        orig_path = doc_input.orig_path
        if orig_path is not None:
            if not orig_path:
                raise ValueError("orig_path must not be empty if provided.")
            if not orig_path.startswith("s3://"):
                raise ValueError("orig_path must start with 's3://'.")
            if not orig_path.lower().endswith((".docx", ".doc", ".pptx", ".ppt")):
                raise ValueError("orig_path must end with .docx, .doc, .pptx, or .ppt.")

        pdf_path = doc_input.pdf_path
        if not pdf_path:
            raise ValueError("pdf_path must be non-empty.")
        if not pdf_path.startswith("s3://"):
            raise ValueError("pdf_path must start with 's3://'.")
        if not skip_ext_check and not pdf_path.lower().endswith(".pdf"):
            raise ValueError("pdf_path must end with .pdf.")
        if self.try_get_doc_by_pdf_path(pdf_path):
            raise DocExistsError(
                message=f"doc with pdf path {pdf_path} already exists.",
                pdf_path=pdf_path,
                pdf_hash=None,
            )

        orig_filesize: int | None = None
        orig_hash: str | None = None
        if orig_path is not None:
            orig_content = read_file(orig_path, allow_local=False)
            orig_filesize = len(orig_content)
            orig_hash = hashlib.sha256(orig_content).hexdigest()

        pdf_content = read_file(pdf_path, allow_local=False)
        pdf_document = PDFDocument(pdf_content)
        if pdf_document.num_pages <= 0:
            raise ValueError(f"PDF document at {pdf_path} has no pages.")

        doc_entity = DocEntity(
            pdf_path=pdf_path,
            pdf_filename=doc_input.pdf_filename,
            pdf_filesize=len(pdf_content),
            pdf_hash=hashlib.sha256(pdf_content).hexdigest(),
            num_pages=pdf_document.num_pages,
            page_width=pdf_document.page_width,
            page_height=pdf_document.page_height,
            metadata=pdf_document.metadata,
            orig_path=orig_path,
            orig_filename=doc_input.orig_filename,
            orig_filesize=orig_filesize,
            orig_hash=orig_hash,
            tags=doc_input.tags or [],
        )

        result = self._insert_elem(Doc, doc_entity)
        if result is None:
            raise DocExistsError(
                message=f"doc with pdf path {pdf_path} already exists.",
                pdf_path=pdf_path,
                pdf_hash=doc_entity.pdf_hash,
            )
        return result

    @_measure_time
    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        self._check_writable()
        if not isinstance(page_input, PageInput):
            raise ValueError("page_input must be a PageInput instance.")

        doc_id = page_input.doc_id
        page_idx = page_input.page_idx

        if doc_id is not None:
            if not doc_id:
                raise ValueError("doc_id must not be empty.")
            if page_idx is None:
                raise ValueError("page_idx must be provided if doc_id is provided.")
            if page_idx < 0:
                raise ValueError("page_idx must be a non-negative integer.")
            doc = self.try_get_doc(doc_id)
            if doc is None:
                raise ValueError(f"Doc with ID {doc_id} does not exist.")
            if page_idx >= doc.num_pages:
                raise ValueError(f"page_idx {page_idx} is beyond {doc.num_pages} pages for doc {doc_id}.")

        image_path = page_input.image_path
        if not image_path:
            raise ValueError("image_path must be non-empty.")
        if not image_path.startswith("s3://"):
            raise ValueError("image_path must start with 's3://'.")
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise ValueError("image_path must end with .jpg, .jpeg, .png or .webp")
        if self.try_get_page_by_image_path(image_path):
            raise ElementExistsError(f"page with image path {image_path} already exists.")

        image_content = read_file(image_path, allow_local=False)
        image = Image.open(io.BytesIO(image_content))
        image = image.convert("RGB")  # Some broken image may raise.

        page_entity = PageEntity(
            doc_id=doc_id,
            page_idx=page_idx,
            image_path=image_path,
            image_filesize=len(image_content),
            image_hash=hashlib.sha256(image_content).hexdigest(),
            image_width=image.width,
            image_height=image.height,
            image_dpi=page_input.image_dpi,
            providers=[],
            tags=page_input.tags or [],
        )

        result = self._insert_elem(Page, page_entity)
        if result is None:
            raise ElementExistsError(f"page with image path {image_path} already exists.")
        return result

    @_measure_time
    def insert_layout(
        self,
        page_id: str,
        provider: str,
        layout_input: LayoutInput,
        insert_blocks=False,
        upsert=False,
    ) -> Layout:
        """Insert a new layout into the database."""
        self._check_writable()
        self._check_name("provider", provider)

        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(layout_input, LayoutInput):
            raise ValueError("layout_data must be a LayoutInput instance.")
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")
        if not upsert and self.try_get_layout_by_page_id_and_provider(page_id, provider):
            raise ElementExistsError(f"Layout for page {page_id} with provider {provider} already exists.")

        self._check_mask_blocks(layout_input.masks)

        # Pre-generate layout ID, used by stored/unstored blocks/contents.
        layout_id = self._new_id(Layout)

        if insert_blocks:
            blocks = self._insert_blocks(page_id, layout_input.blocks, layout_id, provider)
        else:  # use unstored blocks
            blocks = self._normalize_unstored_blocks(page_id, layout_input.blocks, layout_id)

        contents: list[Content] = []
        for cb, block in zip(layout_input.blocks, blocks):
            if cb.content is None:
                continue
            content_input = ContentInput(
                format=cb.format or "text",
                content=cb.content,
                is_human_label=layout_input.is_human_label,
                tags=cb.content_tags,
            )
            if insert_blocks:
                content = self._insert_content(block.id, provider, content_input, layout_id, page_id, upsert)
            else:  # use unstored content
                content = self._normalize_unstored_content(block, provider, content_input, layout_id)
            contents.append(content)

        layout_entity = LayoutEntity(
            id=layout_id,
            page_id=page_id,
            provider=provider,
            masks=[
                MaskBlockEntity(
                    type=mask.type,
                    bbox=[round(num, 4) for num in mask.bbox],
                    angle=mask.angle,
                    attrs=mask.attrs or {},
                )
                for mask in layout_input.masks
            ],
            blocks=[
                LayoutBlockEntity(
                    id=block.id,
                    type=block.type,
                    bbox=block.bbox,
                    angle=block.angle,
                )
                for block in blocks
            ],
            relations=layout_input.relations or [],
            contents=[
                LayoutContentEntity(
                    id=content.id,
                    block_id=content.block_id,
                    format=content.format,
                    content=content.content,
                )
                for content in contents
            ],
            is_human_label=layout_input.is_human_label,
            tags=layout_input.tags or [],
        )

        if upsert:
            query = {"page_id": page_id, "provider": provider}
            result = self._upsert_elem(Layout, query, layout_entity)
        else:  # insert
            result = self._insert_elem(Layout, layout_entity)
            if result is None:
                raise ElementExistsError(
                    f"Layout for page {page_id} with provider {provider} already exists.",
                )

        # add provider to page.providers
        page_data = self._get_coll(Page).find_one_and_update(
            filter={"id": page_id},
            update={"$addToSet": {"providers": provider}},
            projection=EVENT_PROJECTION,
        )
        self._write_event("page", "add_provider", page_data, provider_added=provider)

        return result

    @_measure_time
    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        self._check_writable()
        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(block_input, BlockInput):
            raise ValueError("block_input must be a BlockInput instance.")
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")
        return self._insert_blocks(page_id, [block_input])[0]

    @_measure_time
    def insert_blocks(self, page_id: str, blocks: Sequence[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        self._check_writable()
        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(blocks, list):
            raise ValueError("blocks must be a list of BlockInput instances.")
        if not blocks:
            return []
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")
        return self._insert_blocks(page_id, blocks)

    @_measure_time
    def insert_standalone_block(self, block_input: StandaloneBlockInput) -> Block:
        """Insert a new standalone block (without page)."""
        self._check_writable()
        if not isinstance(block_input, StandaloneBlockInput):
            raise ValueError("block_input must be a StandaloneBlockInput instance.")

        block_type = block_input.type
        if not block_type:
            raise ValueError("block type cannot be empty.")
        if block_type not in BLOCK_TYPES:
            raise ValueError(f"unknown block type: {block_type}.")

        image_path = block_input.image_path
        if not image_path:
            raise ValueError("image_path must be non-empty.")
        if not image_path.startswith("s3://"):
            raise ValueError("image_path must start with 's3://'.")
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise ValueError("image_path must end with .jpg, .jpeg, .png or .webp")
        if self.try_get_block_by_image_path(image_path):
            raise ElementExistsError(f"block with image path {image_path} already exists.")

        image_content = read_file(image_path, allow_local=False)
        image = Image.open(io.BytesIO(image_content))
        image = image.convert("RGB")  # Some broken image may raise.

        block_entity = BlockEntity(
            layout_id=None,
            provider=None,
            page_id=None,
            type=block_type,
            bbox=[0.0, 0.0, 1.0, 1.0],
            angle=None,
            score=None,
            image_path=image_path,
            image_filesize=len(image_content),
            image_hash=hashlib.sha256(image_content).hexdigest(),
            image_width=image.width,
            image_height=image.height,
            versions=[],
            tags=block_input.tags or [],
        )

        # copied from _insert_elem/_upsert_elem
        for tag in block_entity.tags:
            self._check_tag_name(tag)

        coll = self._get_coll(Block)

        now = int(time.time() * 1000)
        elem_data = self._dump_elem(block_entity)
        elem_data["id"] = self._new_id(Block)
        elem_data["rid"] = self._rand_num()
        elem_data["create_time"] = now
        elem_data["update_time"] = now

        result_data = coll.find_one_and_update(
            {"image_path": image_path},
            {"$setOnInsert": elem_data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        if result_data["type"] != block_type:
            raise ElementExistsError(f"block with image path {image_path} already exists.")

        self._write_event("block", "insert", result_data)

        # remove in future.
        for tag in elem_data.get("tags") or []:
            self.add_tag(result_data["id"], tag)

        return self._parse_elem(Block, result_data)

    @_measure_time
    def insert_content(
        self,
        block_id: str,
        version: str,
        content_input: ContentInput,
        upsert=False,
        layout_id: str | None = None,
    ) -> Content:
        """Insert a new content for a block."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_name("version", version)

        if not block_id:
            raise ValueError("block_id must be provided.")
        if not isinstance(content_input, ContentInput):
            raise ValueError("content_input must be a ContentInput instance.")

        format = content_input.format
        if not format:
            raise ValueError("content_input must contain 'format'.")
        if format not in CONTENT_FORMATS:
            raise ValueError(f"unknown content format: {format}.")

        block = self.try_get_block(block_id)
        if block is None:
            raise ValueError(f"Block with ID {block_id} does not exist.")

        content_entity = ContentEntity(
            block_id=block_id,
            version=version,
            page_id=block.page_id,
            format=format,
            content=content_input.content,
            is_human_label=content_input.is_human_label,
            tags=content_input.tags or [],
        )

        if upsert:
            # TODO: upsert may cause difference to layout.content
            query = {"block_id": block_id, "version": version}
            result = self._upsert_elem(Content, query, content_entity, parent_id=layout_id)
        else:  # insert
            result = self._insert_elem(Content, content_entity, parent_id=layout_id)
            if result is None:
                raise ElementExistsError(
                    f"Content for block {block_id} with version {version} already exists.",
                )

        # add version to block.versions
        block_data = self._get_coll(Block).find_one_and_update(
            filter={"id": block_id},
            update={"$addToSet": {"versions": version}},
            projection=EVENT_PROJECTION,
        )
        self._write_event("block", "add_version", block_data, version_added=version)

        return result

    @_measure_time
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a target."""
        # TODO: ensure elem is inserted
        self._check_writable()
        self._check_name("key", key)
        if not isinstance(value_input, ValueInput):
            raise ValueError("value_input must be a ValueInput instance.")

        value = value_input.value
        if not isinstance(value, (str, np.ndarray)):
            raise ValueError("value must be a string or numpy array.")

        value_type = value_input.type
        if not value_type:
            value_type = "str"

        if isinstance(value, np.ndarray):
            value_type = "ndarray"
            value = encode_ndarray(value)

        value_entity = ValueEntity(
            elem_id=elem_id,
            key=key,
            type=value_type,
            value=value,
        )

        result = self._insert_elem(Value, value_entity)
        if result is None:
            raise ElementExistsError(f"Value for element {elem_id} and key {key} already exists.")
        return result

    @_measure_time
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        if any(not isinstance(block, ContentBlockInput) for block in content_blocks):
            raise ValueError("Each content_block must be a ContentBlockInput instance.")

        return self.insert_layout(
            page_id=page_id,
            provider=provider,
            layout_input=LayoutInput(blocks=content_blocks),
            insert_blocks=True,  # TODO: modify in future
            upsert=upsert,
        )

    @_measure_time
    def insert_eval_layout(
        self,
        layout_id: str,
        provider: str,
        blocks: list[EvalLayoutBlock] | None = None,
        relations: list[dict] | None = None,
    ) -> EvalLayout:
        """Insert a new eval layout into the database."""
        self._check_writable()

        if not layout_id:
            raise ValueError("layout_id must be provided.")
        if not provider:
            raise ValueError("provider must be provided.")

        # Verify page and layout exist
        if not self.try_get_layout(layout_id):
            raise ValueError(f"Layout with ID {layout_id} does not exist.")

        blocks = blocks or []
        eval_layout_entity = EvalLayoutEntity(
            layout_id=layout_id,
            provider=provider,
            blocks=[
                EvalLayoutBlockEntity(
                    id=block.id,
                    type=block.type,
                    bbox=block.bbox,
                    angle=block.angle,
                    format=block.format,
                    content=block.content,
                )
                for block in blocks
            ],
            relations=relations or [],
            status=EvalStatus.PENDING,
        )

        result = self._insert_elem(EvalLayout, eval_layout_entity)
        if result is None:
            raise ElementExistsError(f"EvalLayout insertion failed.")
        return result

    @_measure_time
    def insert_eval_content(
        self,
        content_id: str,
        version: str,
        format: str,
        content: str,
    ) -> EvalContent:
        """Insert a new eval content into the database."""
        self._check_writable()

        if not content_id:
            raise ValueError("content_id must be provided.")
        if not version:
            raise ValueError("version must be provided.")

        # Verify block and content exist
        if not self.try_get_content(content_id):
            raise ValueError(f"Content with ID {content_id} does not exist.")

        eval_content_entity = EvalContentEntity(
            content_id=content_id,
            version=version,
            format=format,
            content=content,
            status=EvalStatus.PENDING,
        )

        result = self._insert_elem(EvalContent, eval_content_entity)
        if result is None:
            raise ElementExistsError(f"EvalContent insertion failed.")
        return result

    ###################
    # TASK OPERATIONS #
    ###################

    def _task_stream(self, command: str, priority: int) -> str:
        return f"{command}.{priority}"

    def _build_task_id(self, command: str, priority: int, message_id: str) -> str:
        return f"{command}.{priority}.{message_id}"

    def _parse_task_id(self, task_id: str) -> tuple[str, int, str] | None:
        """return (command, priority, message_id), or None if invalid."""
        match = re.match("^(.+?)\\.(\\d+)\\.(.+)$", task_id)
        if not match:
            return None
        try:
            command, priority_str, message_id = match.groups()
            priority = int(priority_str)
            return (command, priority, message_id)
        except ValueError:
            return None

    def _parse_task(self, task_data: dict, task_id="", status="unknown") -> Task:
        task_args = task_data["args"]
        if isinstance(task_args, str):
            task_args = json.loads(task_args)
        if not isinstance(task_args, dict):
            raise ValueError("task args must be a dict.")
        task = Task(
            id=task_data.get("id", task_id),
            rid=task_data.get("rid", 0),
            target=task_data["target"],
            batch_id=task_data.get("batch_id", ""),
            command=task_data["command"],
            args=task_args,
            priority=task_data.get("priority", -1),
            status=task_data.get("status", status),
            create_user=task_data["create_user"],
            create_time=task_data.get("create_time", 0),
            update_user=task_data.get("update_user"),
            update_time=task_data.get("update_time"),
            error_message=task_data.get("error_message"),
        )
        task.store = self
        return task

    def list_tasks(
        self,
        query: dict | None = None,
        target: str | None = None,
        batch_id: str | None = None,
        command: str | None = None,
        status: str | None = None,
        create_user: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list[Task]:
        """List tasks by filters."""
        query = {
            **(query or {}),
            **({"target": target} if target else {}),
            **({"batch_id": batch_id} if batch_id else {}),
            **({"command": command} if command else {}),
            **({"status": status} if status else {}),
            **({"create_user": create_user} if create_user else {}),
        }
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not target:
            limit = 10

        cursor = self.coll.tasks.find(query, max_time_ms=86400000, batch_size=1000)
        if skip is not None:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)

        tasks = []
        for elem_data in cursor:
            tasks.append(self._parse_task(elem_data))
        return tasks

    @_measure_time
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        task_data = self.coll.tasks.find_one({"id": task_id})

        if task_data is None:
            parsed = self._parse_task_id(task_id)
            if not parsed:
                # Old format: task_id is just message_id, need command parameter
                raise ValueError(f"Old format task_id detected: {task_id}.")

            command, priority, message_id = parsed
            stream = self._task_stream(command, priority)
            task_data = self.redis_stream.manager.get_message(stream, message_id)

        if task_data is None:
            raise ValueError(f"Task not found: {task_id}")

        return self._parse_task(task_data, task_id)

    @_measure_time
    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task."""
        self._check_writable()
        # TODO: ensure the command is defined
        if not target_id:
            raise ValueError("target_id must be provided.")
        if not isinstance(task_input, TaskInput):
            raise ValueError("task_input must be a TaskInput instance.")
        command = task_input.command
        if not command:
            raise ValueError("command must be a non-empty string.")
        args = task_input.args or {}
        if any(not isinstance(k, str) for k in args.keys()):
            raise ValueError("All keys in args must be strings.")
        priority = task_input.priority
        if priority < 0 or priority > self.max_task_priority:
            raise ValueError(f"priority must be between 0 and {self.max_task_priority}")

        task_data = {
            "rid": self._rand_num(),
            "target": target_id,
            "batch_id": task_input.batch_id or "",
            "command": command,
            "args": json.dumps(args),
            "priority": priority,
            "create_user": self.username,
            "create_time": int(time.time() * 1000),
        }

        stream = self._task_stream(command, priority)
        message_id = self.redis_stream.producer.add(stream, fields=task_data)
        task_id = self._build_task_id(command, priority, message_id)

        task = self._parse_task(task_data, task_id, "new")
        if task.batch_id:
            task_data = task.model_dump()
            self.coll.tasks.insert_one(task_data)
        return task

    @_measure_time
    def grab_new_tasks(self, command: str, num=10, hold_sec=3600) -> list[Task]:
        if not isinstance(command, str) or not command:
            raise ValueError("command must be a non-empty string.")
        if hold_sec < 30:
            raise ValueError("hold_sec must be at least 30 seconds.")

        tasks = []
        remaining = num

        for priority in range(self.max_task_priority, -1, -1):
            if remaining <= 0:
                break
            stream = self._task_stream(command, priority)
            consumer = self.redis_stream.get_consumer(stream)
            messages = consumer.read_or_claim(remaining, min_idle_ms=hold_sec * 1000)
            for message in messages:
                task_data = message.fields
                # Use command from message to ensure task_id matches stored data
                msg_command = task_data["command"]
                task_id = self._build_task_id(msg_command, priority, message.id)
                tasks.append(self._parse_task(task_data, task_id, "new"))
                remaining -= 1
                if remaining <= 0:
                    break

        # 兼容老数据：读取老格式的 stream（只有 command，没有 priority）
        if remaining > 0:
            old_stream = command
            consumer = self.redis_stream.get_consumer(old_stream)
            messages = consumer.read_or_claim(remaining, min_idle_ms=hold_sec * 1000)
            for message in messages:
                task_data = message.fields
                msg_command = task_data["command"]
                # Old format: task_id is just message_id
                old_task_id = message.id
                tasks.append(self._parse_task(task_data, old_task_id, "new"))
                remaining -= 1
                if remaining <= 0:
                    break

        return tasks

    @_measure_time
    def update_task(
        self,
        task_id: str,
        command: str,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
        task: Task | None = None,
    ) -> None:
        """Update a task after processed."""
        self._check_writable()
        if not task_id:
            raise ValueError("task ID must be provided.")
        if not command:
            raise ValueError("command must be provided.")
        if status not in ("done", "error", "skipped"):
            raise ValueError("status must be one of 'done', 'error', or 'skipped'.")
        if status == "error" and not error_message:
            raise ValueError("error_message must be provided if status is 'error'.")
        if status == "error" and not task:
            raise ValueError("task must be provided if status is 'error'.")

        parsed = self._parse_task_id(task_id)
        if parsed:
            # New format: {command}{sep}{priority}{sep}{message_id}
            parsed_command, priority, message_id = parsed
            stream = self._task_stream(parsed_command, priority)
        else:
            # Old format: task_id is just message_id, stream is just command
            message_id = task_id
            stream = command

        if self.redis_stream.get_consumer(stream).ack([message_id]) < 1:
            raise TaskMismatchError(
                f"Task with ID {task_id} not found or already updated.",
            )

        if task is None:
            return

        task.status = status
        task.update_user = self.username
        task.update_time = int(time.time() * 1000)
        task.error_message = error_message

        task_data = task.model_dump()
        task_id = task_data.pop("id")
        self.coll.tasks.update_one({"id": task_id}, {"$set": task_data}, upsert=True)

    @_measure_time
    def count_tasks(self, command: str | None = None) -> list[TaskCount]:
        """Count tasks grouped by priority and status."""
        if command:
            commands = set([command])
        else:  # all commands
            keys: list[str] = self.redis_stream.client.keys("*")  # type: ignore
            commands = set([key.split(".")[0] for key in keys])
        task_counts = []
        for command in commands:
            for priority in range(self.max_task_priority, -1, -1):
                stream = self._task_stream(command, priority)
                groups_info = self.redis_stream.manager.groups_info(stream)
                if not groups_info:
                    continue
                for group_info in groups_info:
                    if group_info["name"] == self.redis_stream.consumer_group:
                        read = group_info["entries-read"] if group_info["entries-read"] else 0
                        total = read + group_info["lag"]
                        pending = group_info["lag"]
                        running = group_info["pending"]
                        completed = read - group_info["pending"]
                        task_counts.append(
                            TaskCount(
                                command=command,
                                priority=priority,
                                total=total,
                                pending=pending,
                                running=running,
                                completed=completed,
                            )
                        )
                        break
            # 兼容老数据
            stream = command
            groups_info = self.redis_stream.manager.groups_info(stream)
            if not groups_info:
                continue
            for group_info in groups_info:
                if group_info["name"] == self.redis_stream.consumer_group:
                    read = group_info["entries-read"] if group_info["entries-read"] else 0
                    total = read + group_info["lag"]
                    pending = group_info["lag"]
                    running = group_info["pending"]
                    completed = read - group_info["pending"]
                    task_counts.append(
                        TaskCount(
                            command=command,
                            priority=-1,
                            total=total,
                            pending=pending,
                            running=running,
                            completed=completed,
                        )
                    )
        return task_counts

    # def count_new_tasks(self) -> list[tuple[str, str, int]]:
    #     """Count tasks by command and status."""
    #     results = []
    #     for item in self.coll.tasks.aggregate(
    #         [
    #             {"$match": {"status": "new"}},
    #             {
    #                 "$group": {
    #                     "_id": {
    #                         "command": "$command",
    #                         "path": "$args.path",
    #                         "template": "$args.template",
    #                         "model_name": "$args.model_name",
    #                         "create_user": "$create_user",
    #                     },
    #                     "count": {"$sum": 1},
    #                 }
    #             },
    #         ],
    #         maxTimeMS=10000,
    #     ):
    #         group: dict = item["_id"]
    #         command = group["command"]
    #         if command == "handler" and group.get("path"):
    #             command = group["path"]
    #         other_args = []
    #         if group.get("template"):
    #             other_args.append(group["template"])
    #         if group.get("model_name"):
    #             other_args.append(group["model_name"])
    #         if other_args:
    #             command += f"({','.join(other_args)})"
    #         results.append((command, group["create_user"], item["count"]))
    #     results.sort()
    #     return results

    ##############
    # Embeddings #
    ##############

    @timed_property(ttl=10)
    def embedding_models(self) -> dict[str, EmbeddingModel]:
        return {model.name: model for model in self.list_embedding_models()}

    def list_embedding_models(self) -> list[EmbeddingModel]:
        """List all embedding models in the system."""
        cursor = self.coll.embedding_models.find({}, {"_id": False})
        return [EmbeddingModel(**data) for data in cursor]

    def get_embedding_model(self, name: str) -> EmbeddingModel:
        """Get an embedding model by name."""
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        data = self.coll.embedding_models.find_one({"name": name}, {"_id": False})
        if data is None:
            raise NotFoundError(f"Embedding model [{name}] does not exist.")
        return EmbeddingModel(**data)

    def insert_embedding_model(self, embedding_model: EmbeddingModel) -> EmbeddingModel:
        """Insert a new embedding model to the system."""
        self._check_writable(check_admin=True)
        model_name = embedding_model.name
        if not isinstance(model_name, str):
            raise ValueError(f"Embedding model name must be a string.")
        if not re.match(r"^[a-zA-Z0-9_]+$", model_name):
            raise ValueError(f"Embedding model name must contain only alphanumeric characters and underscores.")
        if not (1 <= embedding_model.dimension <= 32768):
            raise ValueError(f"Embedding model dimension must be between 1 and 32768.")

        # create ES indices for the new embedding model
        page_index_name = f"embeddings.page.{model_name}"
        block_index_name = f"embeddings.block.{model_name}"

        mappings = {
            "properties": {
                "id": {"type": "keyword", "ignore_above": 1024},
                "vector": {
                    "type": "dense_vector",
                    "dims": embedding_model.dimension,
                    "index": True,
                    "similarity": "dot_product" if embedding_model.normalized else "cosine",
                },
            }
        }

        self.es_client.indices.create(index=page_index_name, mappings=mappings)
        self.es_client.indices.create(index=block_index_name, mappings=mappings)

        try:
            data = embedding_model.model_dump()
            self.coll.embedding_models.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
            raise AlreadyExistsError(f"Embedding model [{model_name}] already exists.")

        return embedding_model

    def update_embedding_model(self, name: str, update: EmbeddingModelUpdate) -> EmbeddingModel:
        """Update an existing embedding model in the system."""
        self._check_writable(check_admin=True)
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        data = self.coll.known_users.find_one_and_update(
            {"name": name},
            {"$set": update.model_dump()},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )
        if data is None:
            raise NotFoundError(f"Embedding model [{name}] does not exist.")
        data.pop("_id", None)
        return EmbeddingModel(**data)

    def add_embeddings(self, elem_type: EmbeddableElemType, model: str, embeddings: list[EmbeddingInput]) -> None:
        """Add embeddings to elements of same elem_type."""
        self._check_writable()
        if elem_type not in ("page", "block"):
            raise ValueError(f"elem_type must be 'page' or 'block', got '{elem_type}'.")
        embedding_model: EmbeddingModel = self.embedding_models.get(model)
        if embedding_model is None:
            raise NotFoundError(f"Embedding model [{model}] does not exist.")

        es_documents: list[dict] = []
        for idx, embedding in enumerate(embeddings):
            elem_id = embedding.elem_id
            if not elem_id:
                raise ValueError(f"elem_id must be provided in embedding [{idx}].")
            vector = embedding.vector
            if len(vector) != embedding_model.dimension:
                raise ValueError(f"Vector[{idx}] dim {len(vector)} does not match model dim.")
            if embedding_model.normalized:
                vector = normalize_vector(vector)
            es_documents.append({"id": elem_id, "vector": vector})

        index_name = f"embeddings.{elem_type}.{model}"
        es_writer = EsBulkWriter(self.es_client, index=index_name)
        for document in es_documents:
            es_writer.write(document["id"], document)
        es_writer.flush()

    def search_embeddings(self, elem_type: EmbeddableElemType, model: str, query: EmbeddingQuery) -> list[Embedding]:
        """Search embeddings for elements of same elem_type."""
        if elem_type not in ("page", "block"):
            raise ValueError(f"elem_type must be 'page' or 'block', got '{elem_type}'.")
        embedding_model: EmbeddingModel = self.embedding_models.get(model)
        if embedding_model is None:
            raise NotFoundError(f"Embedding model [{model}] does not exist.")
        vector = query.vector
        if len(vector) != embedding_model.dimension:
            raise ValueError(f"Vector dim {len(vector)} does not match model dim.")
        if embedding_model.normalized:
            vector = normalize_vector(vector)
        k = query.k
        if k <= 0 or k > 10000:
            raise ValueError(f"k must be between 1 and 10000, got {k}.")

        es_query = {
            "knn": {
                "field": "vector",
                "query_vector": vector,
                "k": k,
                "num_candidates": k,
            },
            "_source": ["id", "vector"] if query.show_vector else ["id"],
            "size": k,
        }

        index_name = f"embeddings.{elem_type}.{model}"
        result = self.es_client.search(index=index_name, body=es_query)

        embeddings: list[Embedding] = []
        for item in result["hits"]["hits"]:
            embedding = Embedding(
                elem_id=item["_source"]["id"],
                model=model,
                vector=item["_source"].get("vector"),
                score=item["_score"],
            )
            embeddings.append(embedding)
        return embeddings

    ############
    # Triggers #
    ############

    def _check_trigger_condition(self, condition: TriggerCondition) -> None:
        if condition.elem_type not in ("doc", "page", "layout", "block", "content"):
            raise ValueError(f"Invalid elem_type: {condition.elem_type}.")
        if condition.event_type not in ("insert", "add_tag", "del_tag", "add_provider", "add_version"):
            raise ValueError(f"Invalid event_type: {condition.event_type}.")
        if condition.event_type == "add_provider" and condition.elem_type != "page":
            raise ValueError("add_provider event_type can only be used with elem_type 'page'.")
        if condition.event_type == "add_version" and condition.elem_type != "block":
            raise ValueError("add_version event_type can only be used with elem_type 'block'.")
        if condition.page_providers and condition.elem_type != "page":
            raise ValueError("page_providers can only be used with elem_type 'page'.")
        if condition.layout_provider and condition.elem_type != "layout":
            raise ValueError("layout_provider can only be used with elem_type 'layout'.")
        if condition.block_type and condition.elem_type != "block":
            raise ValueError("block_type can only be used with elem_type 'block'.")
        if condition.block_versions and condition.elem_type != "block":
            raise ValueError("block_versions can only be used with elem_type 'block'.")
        if condition.content_version and condition.elem_type != "content":
            raise ValueError("content_version can only be used with elem_type 'content'.")
        if condition.tag_added and condition.event_type != "add_tag":
            raise ValueError("tag_added can only be used with event_type 'add_tag'.")
        if condition.tag_deleted and condition.event_type != "del_tag":
            raise ValueError("tag_deleted can only be used with event_type 'del_tag'.")
        if condition.provider_added and condition.event_type != "add_provider":
            raise ValueError("provider_added can only be used with event_type 'add_provider'.")
        if condition.version_added and condition.event_type != "add_version":
            raise ValueError("version_added can only be used with event_type 'add_version'.")
        if condition.page_providers and condition.event_type == "insert":
            raise ValueError("page_providers cannot be used with event_type 'insert'.")
        if condition.block_versions and condition.event_type == "insert":
            raise ValueError("block_versions cannot be used with event_type 'insert'.")
        if condition.tags and condition.event_type == "insert":
            raise ValueError("tags cannot be used with event_type 'insert'.")
        for provider in (condition.page_providers or []) + (condition.layout_provider or []) + (condition.provider_added or []):
            self._check_basic_name("provider", provider)
        for version in (condition.block_versions or []) + (condition.content_version or []) + (condition.version_added or []):
            self._check_basic_name("version", version)
        for tag in (condition.tags or []) + (condition.tag_added or []) + (condition.tag_deleted or []):
            self._check_basic_name("tag", tag)
        for block_type in condition.block_type or []:
            if block_type not in BLOCK_TYPES:
                raise ValueError(f"unknown block type: {block_type}.")

    def _check_trigger_action(self, action: TriggerAction) -> None:
        if action.action_type == "add_tag":
            if not action.add_tag:
                raise ValueError("add_tag must be provided for add_tag action.")
            self._check_name("tag", action.add_tag)
        elif action.action_type == "insert_task":
            if not action.insert_task:
                raise ValueError("insert_task must be provided for insert_task action.")
            # TODO: should do the same checking as insert_task
            if not action.insert_task.command:
                raise ValueError("command must be provided in insert_task action.")

    def _check_trigger_input(self, trigger_input: TriggerInput) -> None:
        self._check_name("trigger", trigger_input.name)
        self._check_trigger_condition(trigger_input.condition)
        if not trigger_input.actions:
            raise ValueError("At least one action must be specified.")
        for action in trigger_input.actions:
            self._check_trigger_action(action)

    def list_triggers(self) -> list[Trigger]:
        """List all triggers in the system."""
        cursor = self.coll.triggers.find({}, {"_id": False})
        return [Trigger(**data) for data in cursor]

    def get_trigger(self, trigger_id: str) -> Trigger:
        """Get a trigger by ID."""
        data = self.coll.triggers.find_one({"id": trigger_id}, {"_id": False})
        if data is None:
            raise NotFoundError(f"Trigger with ID [{trigger_id}] does not exist.")
        return Trigger(**data)

    def insert_trigger(self, trigger_input: TriggerInput) -> Trigger:
        """Insert a new trigger to the system."""
        self._check_writable(check_admin=True)
        self._check_trigger_input(trigger_input)

        now = int(time.time() * 1000)

        trigger = Trigger(
            id=f"trigger-{uuid.uuid4()}",
            name=trigger_input.name,
            description=trigger_input.description,
            condition=trigger_input.condition,
            actions=trigger_input.actions,
            create_user=self.username,
            create_time=now,
            update_time=now,
        )

        try:
            data = trigger.model_dump()
            self.coll.triggers.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
            raise AlreadyExistsError(f"Trigger [{trigger_input.name}] already exists.")

        return trigger

    def update_trigger(self, trigger_id: str, trigger_input: TriggerInput) -> Trigger:
        """Update an existing trigger in the system."""
        raise NotImplementedError()

    def delete_trigger(self, trigger_id: str) -> None:
        """Delete a trigger from the system."""
        raise NotImplementedError()

    ##########
    # OTHERS #
    ##########

    def print_times(self) -> None:
        """Print the time taken for each operation."""
        if not self.measure_time:
            print("Time measurement is disabled.")
            return

        if not self.times:
            print("No operations were timed.")
            return

        print("Operation times:")
        for name, elapsed in sorted(self.times.items(), key=lambda x: x[1], reverse=True):
            print(f" - {name}: {elapsed:.4f} seconds")

    def flush(self) -> None:
        """Flush the database changes."""
        if self._event_sink is not None:
            self._event_sink.flush()


# use page-id-block-id ID format.
