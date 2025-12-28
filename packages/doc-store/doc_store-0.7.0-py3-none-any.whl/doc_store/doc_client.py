import json
import os
import warnings
from json import JSONDecodeError
from typing import Any, Iterable, Literal, TypeVar
from urllib.parse import quote

import httpx
import numpy as np

from .config import config
from .interface import (
    AttrInput,
    AttrValueType,
    Block,
    BlockInput,
    Content,
    ContentBlockInput,
    ContentInput,
    Doc,
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
    InputModel,
    KnownName,
    KnownNameInput,
    KnownNameUpdate,
    KnownOptionInput,
    Layout,
    LayoutInput,
    MetricInput,
    Page,
    PageInput,
    StandaloneBlockInput,
    TaggingInput,
    Task,
    TaskCount,
    TaskInput,
    Trigger,
    TriggerInput,
    User,
    UserInput,
    UserUpdate,
    Value,
    ValueInput,
)
from .utils import encode_ndarray, get_username
from .version import version as client_version

T = TypeVar("T", bound=Element)


def _encode_uri_component(s: str) -> str:
    """Encode a string for safe inclusion in a URI component."""
    return quote(s, safe="-_.!~*'()", encoding="utf-8")


def _version_cmp(v1: str, v2: str) -> int:
    """Compare two version strings. return -1 if v1<v2, 0 if v1==v2, 1 if v1>v2."""
    v1_parts, v2_parts = v1.split("."), v2.split(".")
    for p1, p2 in zip(v1_parts, v2_parts):
        try:
            if int(p1) < int(p2):
                return -1
            elif int(p1) > int(p2):
                return 1
            continue
        except Exception:
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
    if len(v1_parts) < len(v2_parts):
        return -1
    elif len(v1_parts) > len(v2_parts):
        return 1
    return 0


class DocClient(DocStoreInterface):
    """HTTP client for DocStore API."""

    def __init__(
        self,
        server_url: str | None = None,
        prefix: str = "/api/v1",
        timeout: int = 300,
        connect_timeout: int = 30,
        decode_value=True,
    ):
        """
        Initialize DocClient.

        Args:
            server_url: Base URL of the DocStore API server
            timeout: Read timeout in seconds (for stream requests, this is per-chunk)
            connect_timeout: Connection timeout in seconds
        """
        super().__init__()

        proxy_envs = [env for env in os.environ.keys() if env.lower() in ("http_proxy", "https_proxy")]
        if len(proxy_envs) > 0:
            warnings.warn(
                f"HTTP proxy environment variables {proxy_envs} are set, which may affect DocClient behavior."
                " Please unset them if unintended.",
                UserWarning,
            )

        if not server_url:
            server_url = config.server.url
        if not server_url:
            raise ValueError("server_url must be provided either in argument or config.")
        self.server_url = server_url.rstrip("/")
        self.prefix = prefix.rstrip("/")
        self.decode_value = decode_value

        self.client = httpx.Client(
            headers={
                "X-Username": get_username(),
            },
            timeout=httpx.Timeout(
                connect=connect_timeout,
                read=timeout,
                write=timeout,
                pool=connect_timeout,
            ),
        )

        server_info = self.health_check()
        server_version = server_info.get("version", "")
        min_required_version = server_info.get("min_required_version", "")

        if _version_cmp(client_version, min_required_version) < 0:
            raise RuntimeError(
                f"DocClient version ({client_version}) is lower than the minimum required server version"
                f" ({min_required_version}). Please upgrade the DocClient to ensure compatibility."
            )
        if server_version != client_version:
            warnings.warn(
                f"DocClient version ({client_version}) does not match server version ({server_version})."
                " This may lead to compatibility issues.",
                UserWarning,
            )

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _decode_json(self, response: httpx.Response):
        try:
            return response.json()
        except JSONDecodeError as e:
            raise JSONDecodeError(
                f"Response text:\n\n{response.text}\n---\n{e.msg}",
                e.doc,
                e.pos,
            ) from None

    def _request(
        self,
        method: str,
        path: str,
        json_data: dict | list | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        """Make HTTP request to the server."""
        url = f"{self.server_url}{self.prefix}{path}"

        retries = 5
        response = None
        exception = None
        while True:
            if retries < 0:
                break
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                )
            except httpx.RemoteProtocolError as e:
                # httpx.RemoteProtocolError: Server disconnected without sending a response.
                exception = e
                retries -= 1
                continue
            except httpx.ReadError as e:
                # httpx.ReadError: [Errno 104] Connection reset by peer
                exception = e
                retries -= 1
                continue
            if response.status_code == 502:
                # 502 Bad Gateway
                retries -= 1
                continue
            # Successful request or other HTTP error status
            break

        if response is None:
            raise exception if exception else Exception("Failed to make request to server.")
        if response.status_code == 400:
            error_data = self._decode_json(response)
            raise ValueError(error_data.get("message", "Bad request"))
        elif response.status_code == 403:
            error_data = self._decode_json(response)
            raise PermissionError(error_data.get("message", "Permission denied"))
        elif response.status_code == 404:
            error_data = self._decode_json(response)
            raise ElementNotFoundError(error_data.get("message", "Element not found"))
        elif response.status_code == 409:
            error_data = self._decode_json(response)
            raise ElementExistsError(error_data.get("message", "Element already exists"))
        elif response.status_code == 422:
            raise ValueError(f"Validation Error {response.text}")
        elif response.status_code >= 400:
            raise Exception(f"Status: {response.status_code}, Response text: {response.text}")
        return response

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Make GET request and return JSON response."""
        response = self._request("GET", path, params=params)
        return self._decode_json(response)

    def _post(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> dict | list:
        """Make POST request and return JSON response."""
        response = self._request("POST", path, json_data=json_data, params=params)
        return self._decode_json(response)

    def _put(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> dict | None:
        """Make PUT request and return JSON response."""
        response = self._request("PUT", path, json_data=json_data, params=params)
        if response.status_code == 204 or len(response.content) == 0:
            return None
        return self._decode_json(response)

    def _patch(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> dict | None:
        """Make PATCH request and return JSON response."""
        response = self._request("PATCH", path, json_data=json_data, params=params)
        if response.status_code == 204 or len(response.content) == 0:
            return None
        return self._decode_json(response)

    def _delete(self, path: str) -> dict | None:
        """Make DELETE request and return JSON response."""
        response = self._request("DELETE", path)
        if response.status_code == 204 or len(response.content) == 0:
            return None
        return self._decode_json(response)

    def _stream(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> Iterable[dict]:
        """Make POST request and stream JSON lines response."""
        url = f"{self.server_url}{self.prefix}{path}"

        with self.client.stream("POST", url, json=json_data, params=params) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def _dump_elem(self, elem_input: InputModel) -> dict:
        """Dump element input model to dict for JSON serialization."""
        if isinstance(elem_input, LayoutInput):
            return {
                "blocks": [self._dump_elem(b) for b in elem_input.blocks],
                "relations": elem_input.relations,
                "tags": elem_input.tags,
            }
        return elem_input.model_dump()

    def _parse_elem(self, elem_type: type[T], elem_data: dict) -> T:
        """Parse element data into the specified type."""
        if elem_type == Layout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [self._parse_elem(Block, b) for b in blocks]
        elif elem_type == EvalLayout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [EvalLayoutBlock(**b) if isinstance(b, dict) else b for b in blocks]
        elem_object = elem_type(**elem_data)
        elem_object.store = self
        if isinstance(elem_object, Value) and self.decode_value:
            elem_object.decode()
        return elem_object

    ####################
    # READ OPERATIONS  #
    ####################

    def health_check(self, show_stats: bool = False) -> dict:
        """Check the health of the doc store."""
        params = {"show_stats": show_stats} if show_stats else None
        return self._get(f"/health", params=params)

    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        data = self._get(f"/docs/{doc_id}")
        return self._parse_elem(Doc, data)

    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        data = self._get(f"/docs/pdf-path/{_encode_uri_component(pdf_path)}")
        return self._parse_elem(Doc, data)

    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        data = self._get(f"/docs/pdf-hash/{pdf_hash}")
        return self._parse_elem(Doc, data)

    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        data = self._get(f"/pages/{page_id}")
        return self._parse_elem(Page, data)

    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        data = self._get(f"/pages/image-path/{_encode_uri_component(image_path)}")
        return self._parse_elem(Page, data)

    def get_layout(self, layout_id: str, expand: bool = False) -> Layout:
        """Get a layout by its ID."""
        data = self._get(f"/layouts/{layout_id}", params={"expand": expand})
        return self._parse_elem(Layout, data)

    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str, expand: bool = False) -> Layout:
        """Get a layout by its page ID and provider."""
        data = self._get(f"/pages/{page_id}/layouts/{provider}", params={"expand": expand})
        return self._parse_elem(Layout, data)

    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        data = self._get(f"/blocks/{block_id}")
        return self._parse_elem(Block, data)

    def get_block_by_image_path(self, image_path: str) -> Block:
        """Get a block by its image path."""
        data = self._get(f"/blocks/image-path/{_encode_uri_component(image_path)}")
        return self._parse_elem(Block, data)

    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        data = self._get(f"/pages/{page_id}/super-block")
        return self._parse_elem(Block, data)

    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        data = self._get(f"/contents/{content_id}")
        return self._parse_elem(Content, data)

    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        data = self._get(f"/blocks/{block_id}/contents/{version}")
        return self._parse_elem(Content, data)

    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        data = self._get(f"/values/{value_id}")
        return self._parse_elem(Value, data)

    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its elem_id and key."""
        data = self._get(f"/elements/{elem_id}/values/{key}")
        return self._parse_elem(Value, data)

    def get_eval_layout(self, eval_layout_id: str) -> EvalLayout:
        """Get an eval layout by its ID."""
        data = self._get(f"/evallayouts/{eval_layout_id}")
        return self._parse_elem(EvalLayout, data)

    def get_eval_content(self, eval_content_id: str) -> EvalContent:
        """Get an eval content by its ID."""
        data = self._get(f"/evalcontents/{eval_content_id}")
        return self._parse_elem(EvalContent, data)

    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "providers", "provider", "versions", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get all distinct values for a specific field of an element type."""
        data = self._post(f"/distinct/{elem_type}/{field}", json_data=query)
        assert isinstance(data, list)
        return data

    def find(
        self,
        elem_type: ElemType | type,
        query: dict | list[dict] | None = None,
        query_from: ElemType | type | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Element]:
        """Find elements of a specific type matching the query."""
        # Convert class types to elem_type strings
        if isinstance(elem_type, type):
            elem_type = elem_type.__name__.lower()  # type: ignore
        if isinstance(query_from, type):
            query_from = query_from.__name__.lower()  # type: ignore

        params = {}
        if query_from:
            params["query_from"] = query_from
        if skip is not None:
            params["skip"] = skip
        if limit is not None:
            params["limit"] = limit

        # Map elem_type to element class
        elem_classes = {
            "doc": Doc,
            "page": Page,
            "layout": Layout,
            "block": Block,
            "content": Content,
            "value": Value,
            "task": Task,
            "eval_layout": EvalLayout,
            "eval_content": EvalContent,
        }

        assert isinstance(elem_type, str)
        elem_cls = elem_classes.get(elem_type, Element)

        for data in self._stream(f"/stream/{elem_type}", json_data=query, params=params):
            yield self._parse_elem(elem_cls, data)

    def count(
        self,
        elem_type: ElemType | type,
        query: dict | list[dict] | None = None,
        query_from: ElemType | type | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        # Convert class types to elem_type strings
        if isinstance(elem_type, type):
            elem_type = elem_type.__name__.lower()  # type: ignore
        if isinstance(query_from, type):
            query_from = query_from.__name__.lower()  # type: ignore

        params = {}
        if query_from:
            params["query_from"] = query_from
        if estimated:
            params["estimated"] = estimated

        data = self._post(f"/count/{elem_type}", json_data=query, params=params)
        assert isinstance(data, int)
        return data

    ####################
    # WRITE OPERATIONS #
    ####################

    def add_tag(self, elem_id: str, tag: str) -> None:
        """Add tag to an element."""
        self._put(f"/elements/{elem_id}/tags/{tag}")

    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        self._delete(f"/elements/{elem_id}/tags/{tag}")

    def batch_add_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch add tag to multiple elements."""
        self._post(f"/batch/{elem_type}/add-tag/{tag}", json_data=elem_ids)

    def batch_del_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch delete tag from multiple elements."""
        self._post(f"/batch/{elem_type}/del-tag/{tag}", json_data=elem_ids)

    def add_attr(self, elem_id: str, name: str, attr_input: AttrInput) -> None:
        """Add an attribute to an element."""
        input_data = self._dump_elem(attr_input)
        self._put(f"/elements/{elem_id}/attrs/{name}", json_data=input_data)

    def add_attrs(self, elem_id: str, attrs: dict[str, AttrValueType]) -> None:
        """Add multiple attributes to an element."""
        self._patch(f"/elements/{elem_id}/attrs", json_data=attrs)

    def del_attr(self, elem_id: str, name: str) -> None:
        """Delete an attribute from an element."""
        self._delete(f"/elements/{elem_id}/attrs/{name}")

    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        input_data = self._dump_elem(metric_input)
        self._put(f"/elements/{elem_id}/metrics/{name}", json_data=input_data)

    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        self._delete(f"/elements/{elem_id}/metrics/{name}")

    def tagging(self, elem_id: str, tagging_input: TaggingInput) -> None:
        """Add/Delete tags, attributes, and metrics to/from an element."""
        input_data = self._dump_elem(tagging_input)
        self._post(f"/elements/{elem_id}/tagging", json_data=input_data)

    def batch_tagging(self, elem_type: ElemType, inputs: list[ElementTagging]) -> None:
        """Batch add/delete tags, attributes, and metrics to/from multiple elements."""
        input_data = [self._dump_elem(t) for t in inputs]
        self._post(f"/batch/{elem_type}/tagging", json_data=input_data)

    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a element."""
        if isinstance(value_input.value, np.ndarray):
            value_input = ValueInput(
                value=encode_ndarray(value_input.value),
                type="ndarray",
            )
        input_data = self._dump_elem(value_input)
        data = self._put(f"/elements/{elem_id}/values/{key}", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Value, data)

    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        input_data = self._dump_elem(doc_input)
        data = self._post("/docs", json_data=input_data, params={"skip_ext_check": skip_ext_check})
        assert isinstance(data, dict)
        return self._parse_elem(Doc, data)

    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        input_data = self._dump_elem(page_input)
        data = self._post("/pages", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Page, data)

    def insert_layout(
        self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=False, upsert=False
    ) -> Layout:
        """Insert a new layout into the database."""
        input_data = self._dump_elem(layout_input)
        data = self._put(
            f"/pages/{page_id}/layouts/{provider}",
            json_data=input_data,
            params={"insert_blocks": insert_blocks, "upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Layout, data)

    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        input_data = self._dump_elem(block_input)
        data = self._post(f"/pages/{page_id}/blocks", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Block, data)

    def insert_blocks(self, page_id: str, blocks: list[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        input_data = [self._dump_elem(b) for b in blocks]
        data = self._post(f"/pages/{page_id}/blocks/batch", json_data=input_data)
        assert isinstance(data, list)
        return [self._parse_elem(Block, block_data) for block_data in data]

    def insert_standalone_block(self, block_input: StandaloneBlockInput) -> Block:
        """Insert a new standalone block (without page)."""
        input_data = self._dump_elem(block_input)
        data = self._post("/blocks", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Block, data)

    def insert_content(self, block_id: str, version: str, content_input: ContentInput, upsert=False) -> Content:
        """Insert a new content for a block."""
        input_data = self._dump_elem(content_input)
        data = self._put(
            f"/blocks/{block_id}/contents/{version}",
            json_data=input_data,
            params={"upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Content, data)

    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        input_data = [self._dump_elem(b) for b in content_blocks]
        data = self._put(
            f"/pages/{page_id}/content-blocks-layouts/{provider}",
            json_data=input_data,
            params={"upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Layout, data)

    def insert_eval_layout(
        self,
        layout_id: str,
        provider: str,
        blocks: list[EvalLayoutBlock] | None = None,
        relations: list[dict] | None = None,
    ) -> EvalLayout:
        """Insert a new eval layout into the database."""
        input_data = {
            "layout_id": layout_id,
            "provider": provider,
            "blocks": [b.model_dump() for b in blocks] if blocks else [],
            "relations": relations or [],
        }
        data = self._post("/evallayouts", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(EvalLayout, data)

    def insert_eval_content(
        self,
        content_id: str,
        version: str,
        format: str,
        content: str,
    ) -> EvalContent:
        """Insert a new eval content into the database."""
        input_data = {
            "content_id": content_id,
            "version": version,
            "format": format,
            "content": content,
        }
        data = self._post("/evalcontents", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(EvalContent, data)

    ###################
    # TASK OPERATIONS #
    ###################

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
        params = {
            **({"target": target} if target else {}),
            **({"batch_id": batch_id} if batch_id else {}),
            **({"command": command} if command else {}),
            **({"status": status} if status else {}),
            **({"create_user": create_user} if create_user else {}),
            **({"skip": skip} if skip is not None else {}),
            **({"limit": limit} if limit is not None else {}),
        }
        data = self._post(f"/list/tasks", json_data=query, params=params)
        assert isinstance(data, list)
        return [Task(**task_data) for task_data in data]

    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        data = self._get(f"/tasks/{task_id}")
        return Task(**data)

    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task into the database."""
        input_data = self._dump_elem(task_input)
        data = self._post(f"/elements/{target_id}/tasks", json_data=input_data)
        assert isinstance(data, dict)
        return Task(**data)

    def grab_new_tasks(self, command: str, num=10, hold_sec=3600) -> list[Task]:
        """Grab new tasks for processing."""
        params = {"num": num, "hold_sec": hold_sec}
        data = self._post(f"/grab-new-tasks/{command}", params=params)
        return [Task(**task_data) for task_data in data]

    def update_task(
        self,
        task_id: str,
        command: str,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
        task: Task | None = None,
    ) -> None:
        """Update a task after processing."""
        params = {"command": command, "status": status}
        if error_message:
            params["error_message"] = error_message
        input_data = task.model_dump() if task else None
        self._post(f"/update-grabbed-task/{task_id}", json_data=input_data, params=params)

    def count_tasks(self, command: str | None = None) -> list[TaskCount]:
        """Count tasks grouped by priority and status."""
        params = {"command": command} if command else {}
        data = self._get("/count-tasks", params=params)
        assert isinstance(data, list)
        return [TaskCount(**task_count_data) for task_count_data in data]

    #########################
    # MANAGEMENT OPERATIONS #
    #########################

    def list_users(self) -> list[User]:
        """List all users in the system."""
        data = self._get("/users")
        assert isinstance(data, list)
        return [User(**user_data) for user_data in data]

    def get_user(self, name: str) -> User:
        """Get a user by name."""
        data = self._get(f"/users/{name}")
        assert isinstance(data, dict)
        return User(**data)

    def insert_user(self, user_input: UserInput) -> User:
        """Add a new user to the system."""
        input_data = user_input.model_dump()
        data = self._post("/users", json_data=input_data)
        assert isinstance(data, dict)
        return User(**data)

    def update_user(self, name: str, user_update: UserUpdate) -> User:
        """Update an existing user in the system."""
        input_data = user_update.model_dump()
        data = self._put(f"/users/{name}", json_data=input_data)
        assert isinstance(data, dict)
        return User(**data)

    def list_known_names(self) -> list[KnownName]:
        """List all known tag/attribute/metric names in the system."""
        data = self._get("/known-names")
        assert isinstance(data, list)
        return [KnownName(**name_data) for name_data in data]

    def insert_known_name(self, known_name_input: KnownNameInput) -> KnownName:
        """Add a new known tag/attribute/metric name to the system."""
        input_data = known_name_input.model_dump()
        data = self._post("/known-names", json_data=input_data)
        assert isinstance(data, dict)
        return KnownName(**data)

    def update_known_name(self, name: str, known_name_update: KnownNameUpdate) -> KnownName:
        """Update an existing known tag/attribute/metric name in the system."""
        input_data = known_name_update.model_dump()
        data = self._put(f"/known-names/{name}", json_data=input_data)
        assert isinstance(data, dict)
        return KnownName(**data)

    def add_known_option(self, attr_name: str, option_name: str, option_input: KnownOptionInput) -> None:
        """Add/Update a new known option to a known attribute name."""
        input_data = option_input.model_dump()
        self._put(f"/known-names/{attr_name}/options/{option_name}", json_data=input_data)

    def del_known_option(self, attr_name: str, option_name: str) -> None:
        """Delete a known option from a known attribute name."""
        self._delete(f"/known-names/{attr_name}/options/{option_name}")

    def list_embedding_models(self) -> list[EmbeddingModel]:
        """List all embedding models in the system."""
        data = self._get("/embedding-models")
        assert isinstance(data, list)
        return [EmbeddingModel(**model_data) for model_data in data]

    def get_embedding_model(self, name: str) -> EmbeddingModel:
        """Get an embedding model by name."""
        data = self._get(f"/embedding-models/{name}")
        assert isinstance(data, dict)
        return EmbeddingModel(**data)

    def insert_embedding_model(self, embedding_model: EmbeddingModel) -> EmbeddingModel:
        """Insert a new embedding model to the system."""
        input_data = embedding_model.model_dump()
        data = self._post("/embedding-models", json_data=input_data)
        assert isinstance(data, dict)
        return EmbeddingModel(**data)

    def update_embedding_model(self, name: str, update: EmbeddingModelUpdate) -> EmbeddingModel:
        """Update an existing embedding model in the system."""
        input_data = update.model_dump()
        data = self._put(f"/embedding-models/{name}", json_data=input_data)
        assert isinstance(data, dict)
        return EmbeddingModel(**data)

    def add_embeddings(self, elem_type: EmbeddableElemType, model: str, embeddings: list[EmbeddingInput]) -> None:
        """Add embeddings to elements of same elem_type."""
        input_data = [self._dump_elem(e) for e in embeddings]
        self._post(f"/batch/{elem_type}/add-embedding/{model}", json_data=input_data)

    def search_embeddings(self, elem_type: EmbeddableElemType, model: str, query: EmbeddingQuery) -> list[Embedding]:
        """Search embeddings for elements of same elem_type."""
        input_data = self._dump_elem(query)
        data = self._post(f"/search/{elem_type}/by-embedding/{model}", json_data=input_data)
        assert isinstance(data, list)
        return [Embedding(**emb_data) for emb_data in data]

    def list_triggers(self) -> list[Trigger]:
        """List all triggers in the system."""
        data = self._get("/triggers")
        assert isinstance(data, list)
        return [Trigger(**trigger_data) for trigger_data in data]

    def get_trigger(self, trigger_id: str) -> Trigger:
        """Get a trigger by ID."""
        data = self._get(f"/triggers/{trigger_id}")
        assert isinstance(data, dict)
        return Trigger(**data)

    def insert_trigger(self, trigger_input: TriggerInput) -> Trigger:
        """Insert a new trigger to the system."""
        input_data = self._dump_elem(trigger_input)
        data = self._post("/triggers", json_data=input_data)
        assert isinstance(data, dict)
        return Trigger(**data)

    def update_trigger(self, trigger_id: str, trigger_input: TriggerInput) -> Trigger:
        """Update an existing trigger in the system."""
        input_data = self._dump_elem(trigger_input)
        data = self._put(f"/triggers/{trigger_id}", json_data=input_data)
        assert isinstance(data, dict)
        return Trigger(**data)

    def delete_trigger(self, trigger_id: str) -> None:
        """Delete a trigger from the system."""
        self._delete(f"/triggers/{trigger_id}")
