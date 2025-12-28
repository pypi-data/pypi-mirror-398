import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Iterable, Literal

import anyio.to_thread
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# from .base_routes import BaseRoutes, route
from .doc_store import DocStore
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
    KnownName,
    KnownNameInput,
    KnownNameUpdate,
    KnownOptionInput,
    Layout,
    LayoutInput,
    MetricInput,
    NotFoundError,
    Page,
    PageInput,
    StandaloneBlockInput,
    TaggingInput,
    Task,
    TaskCount,
    TaskInput,
    Trigger,
    TriggerInput,
    UnauthorizedError,
    User,
    UserInput,
    UserUpdate,
    Value,
    ValueInput,
)

DEFAULT_LIMIT = 10
INJECT: Any = None
_global_index = 0


def route(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    *,
    tags: list[str],
):
    global _global_index
    _global_index += 1

    def decorator(func):
        func._route_info = {
            "index": _global_index,
            "method": method,
            "path": path,
            "tags": tags,
        }
        return func

    return decorator


async def add_process_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["x-process-time"] = str(process_time)
    return response


def iter_response(iterable: Iterable[Element]) -> Iterable[bytes]:
    for item in iterable:
        item_dict = item.model_dump()
        json_string = json.dumps(item_dict, ensure_ascii=False)
        yield (json_string + "\n").encode("utf-8")


# class DocRoutes(BaseRoutes, DocStoreInterface):


@asynccontextmanager
async def lifespan(app: FastAPI):
    limiter = anyio.to_thread.current_default_thread_limiter()
    before_adjust = limiter.total_tokens
    limiter.total_tokens = 400  # increased from 40 to 400
    print(f"Adjusted thread limit from {before_adjust} to {limiter.total_tokens}")
    yield


class DocServer(DocStoreInterface):
    def __init__(self, store: DocStore) -> None:
        super().__init__()
        self.store = store
        self.store_cache = {}
        self.logger = logging.getLogger(__name__)
        self.pid = os.getpid()

        self.app = FastAPI(
            title="DocStore API",
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json",
            lifespan=lifespan,
        )

        self.app.middleware("http")(add_process_time)
        self.app.middleware("http")(self.exception_middleware)
        # self.app.add_exception_handler(Exception, self.exception_handler)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Lookup routes
        routes = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_route_info"):
                route_info = getattr(attr, "_route_info")
                routes.append((route_info["index"], route_info, attr))

        # Register routes
        api_router = APIRouter(prefix="/api/v1")
        for _, route_info, endpoint in sorted(routes):
            api_router.add_api_route(
                path=route_info["path"],
                endpoint=endpoint,
                methods=[route_info["method"]],
                tags=route_info["tags"],
            )

        self.app.include_router(api_router)

    async def exception_middleware(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return self.exception_handler(request, e)

    def exception_handler(self, _: Request, e: Exception):
        if isinstance(e, UnauthorizedError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "UnauthorizedError", "message": str(e)},
            )
        elif isinstance(e, ElementNotFoundError):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "ElementNotFoundError", "message": str(e)},
            )
        elif isinstance(e, NotFoundError):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "NotFoundError", "message": str(e)},
            )
        elif isinstance(e, ElementExistsError):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"error": "ElementExistsError", "message": str(e)},
            )
        elif isinstance(e, AlreadyExistsError):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"error": "AlreadyExistsError", "message": str(e)},
            )
        elif isinstance(e, PermissionError):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "PermissionError", "message": str(e)},
            )
        elif isinstance(e, ValueError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "ValueError", "message": str(e)},
            )
        self.logger.error("Unhandled exception occurred", exc_info=e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": str(e)},
        )

    def get_request_user(self, req: Request) -> str:
        username = req.headers.get("X-Username")
        if not username:
            username = "tmp"
        return username

    def get_store(self, req: Request) -> DocStore:
        username = self.get_request_user(req)
        store = self.store_cache.get(username)
        if not store:
            store = self.store.impersonate(username)
            self.store_cache[username] = store
        return store

    @route("GET", "/ping", tags=["health"])
    def ping(self, sleep: float | None = None, req: Request = INJECT) -> dict:
        if sleep is not None and sleep > 0:
            time.sleep(sleep)
        client = f"{req.client.host}:{req.client.port}" if req.client else None
        return {"message": "pong", "pid": self.pid, "client": client, "sleep": sleep}

    @route("GET", "/aio_ping", tags=["health"])
    async def aio_ping(self, sleep: float | None = None, req: Request = INJECT) -> dict:
        if sleep is not None and sleep > 0:
            await asyncio.sleep(sleep)
        client = f"{req.client.host}:{req.client.port}" if req.client else None
        return {"message": "pong", "pid": self.pid, "client": client, "sleep": sleep}

    @route("GET", "/health", tags=["health"])
    def health_check(self, show_stats: bool = False, req: Request = INJECT) -> dict:
        return self.store.health_check(show_stats=show_stats)

    @route("GET", "/docs/{doc_id}", tags=["docs"])
    def get_doc(self, doc_id: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc(doc_id)

    @route("GET", "/docs/pdf-path/{pdf_path:path}", tags=["docs"])
    def get_doc_by_pdf_path(self, pdf_path: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc_by_pdf_path(pdf_path)

    @route("GET", "/docs/pdf-hash/{pdf_hash:path}", tags=["docs"])
    def get_doc_by_pdf_hash(self, pdf_hash: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc_by_pdf_hash(pdf_hash)

    @route("GET", "/pages/{page_id}", tags=["pages"])
    def get_page(self, page_id: str, req: Request = INJECT) -> Page:
        return self.get_store(req).get_page(page_id)

    @route("GET", "/pages/image-path/{image_path:path}", tags=["pages"])
    def get_page_by_image_path(self, image_path: str, req: Request = INJECT) -> Page:
        return self.get_store(req).get_page_by_image_path(image_path)

    @route("GET", "/layouts/{layout_id}", tags=["layouts"])
    def get_layout(self, layout_id: str, expand: bool = False, req: Request = INJECT) -> Layout:
        return self.get_store(req).get_layout(layout_id, expand)

    @route("GET", "/pages/{page_id}/layouts/{provider}", tags=["layouts"])
    def get_layout_by_page_id_and_provider(
        self, page_id: str, provider: str, expand: bool = False, req: Request = INJECT
    ) -> Layout:
        return self.get_store(req).get_layout_by_page_id_and_provider(page_id, provider, expand)

    @route("GET", "/blocks/{block_id}", tags=["blocks"])
    def get_block(self, block_id: str, req: Request = INJECT) -> Block:
        return self.get_store(req).get_block(block_id)

    @route("GET", "/blocks/image-path/{image_path:path}", tags=["blocks"])
    def get_block_by_image_path(self, image_path: str, req: Request = INJECT) -> Block:
        return self.get_store(req).get_block_by_image_path(image_path)

    @route("GET", "/pages/{page_id}/super-block", tags=["blocks"])
    def get_super_block(self, page_id: str, req: Request = INJECT) -> Block:
        return self.get_store(req).get_super_block(page_id)

    @route("GET", "/contents/{content_id}", tags=["contents"])
    def get_content(self, content_id: str, req: Request = INJECT) -> Content:
        return self.get_store(req).get_content(content_id)

    @route("GET", "/blocks/{block_id}/contents/{version}", tags=["contents"])
    def get_content_by_block_id_and_version(self, block_id: str, version: str, req: Request = INJECT) -> Content:
        return self.get_store(req).get_content_by_block_id_and_version(block_id, version)

    @route("GET", "/values/{value_id}", tags=["values"])
    def get_value(self, value_id: str, req: Request = INJECT) -> Value:
        return self.get_store(req).get_value(value_id)

    @route("GET", "/elements/{elem_id}/values/{key}", tags=["values"])
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str, req: Request = INJECT) -> Value:
        return self.get_store(req).get_value_by_elem_id_and_key(elem_id, key)

    @route("GET", "/tasks/{task_id}", tags=["tasks"])
    def get_task(self, task_id: str, req: Request = INJECT) -> Task:
        return self.get_store(req).get_task(task_id)

    @route("GET", "/evallayouts/{eval_layout_id}", tags=["evaluations"])
    def get_eval_layout(self, eval_layout_id: str, req: Request = INJECT):
        """Get an eval layout by its ID."""
        return self.get_store(req).get_eval_layout(eval_layout_id)

    @route("GET", "/evalcontents/{eval_content_id}", tags=["evaluations"])
    def get_eval_content(self, eval_content_id: str, req: Request = INJECT):
        """Get an eval content by its ID."""
        return self.get_store(req).get_eval_content(eval_content_id)

    @route("POST", "/distinct/{elem_type}/{field}", tags=["others"])
    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "providers", "provider", "versions", "version"],
        query: dict | None = None,
        req: Request = INJECT,
    ) -> list[str]:
        return self.get_store(req).distinct_values(elem_type, field, query)

    @route("POST", "/stream/{elem_type}", tags=["others"])
    def find(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> Iterable[Element]:
        it = self.get_store(req).find(elem_type, query, query_from, skip, limit)
        return StreamingResponse(iter_response(it), media_type="text/plain; charset=utf8")  # type: ignore

    @route("POST", "/list/docs", tags=["docs"])
    def list_docs(
        self,
        query: dict | list[dict] | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Doc]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        else:  # limit is None
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_docs(query, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/pages", tags=["pages"])
    def list_pages(
        self,
        query: dict | list[dict] | None = None,
        doc_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Page]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not doc_id:
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_pages(query, doc_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/layouts", tags=["layouts"])
    def list_layouts(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Layout]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not page_id:
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_layouts(query, page_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/blocks", tags=["blocks"])
    def list_blocks(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Block]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not page_id:
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_blocks(query, page_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/contents", tags=["contents"])
    def list_contents(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        block_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Content]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not (page_id or block_id):
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_contents(query, page_id, block_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/values", tags=["values"])
    def list_values(
        self,
        query: dict | list[dict] | None = None,
        elem_id: str | None = None,
        key: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Value]:
        if skip is not None:
            skip = max(0, skip)
        if limit is not None:
            limit = max(1, limit)
        elif not elem_id:
            limit = DEFAULT_LIMIT
        it = self.get_store(req).find_values(query, elem_id, key, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/tasks", tags=["tasks"])
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
        req: Request = INJECT,
    ) -> list[Task]:
        return self.get_store(req).list_tasks(
            query=query,
            target=target,
            batch_id=batch_id,
            command=command,
            status=status,
            create_user=create_user,
            skip=skip,
            limit=limit,
        )

    @route("POST", "/count/{elem_type}", tags=["others"])
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
        req: Request = INJECT,
    ) -> int:
        return self.get_store(req).count(elem_type, query, query_from, estimated)

    ####################
    # WRITE OPERATIONS #
    ####################

    @route("PUT", "/elements/{elem_id}/tags/{tag}", tags=["tags"])
    def add_tag(self, elem_id: str, tag: str, req: Request = INJECT) -> None:
        return self.get_store(req).add_tag(elem_id, tag)

    @route("DELETE", "/elements/{elem_id}/tags/{tag}", tags=["tags"])
    def del_tag(self, elem_id: str, tag: str, req: Request = INJECT) -> None:
        return self.get_store(req).del_tag(elem_id, tag)

    @route("POST", "/batch/{elem_type}/add-tag/{tag}", tags=["tags"])
    def batch_add_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str], req: Request = INJECT) -> None:
        return self.get_store(req).batch_add_tag(elem_type, tag, elem_ids)

    @route("POST", "/batch/{elem_type}/del-tag/{tag}", tags=["tags"])
    def batch_del_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str], req: Request = INJECT) -> None:
        return self.get_store(req).batch_del_tag(elem_type, tag, elem_ids)

    @route("PUT", "/elements/{elem_id}/attrs/{name}", tags=["tags"])
    def add_attr(self, elem_id: str, name: str, attr_input: AttrInput, req: Request = INJECT) -> None:
        return self.get_store(req).add_attr(elem_id, name, attr_input)

    @route("PATCH", "/elements/{elem_id}/attrs", tags=["tags"])
    def add_attrs(self, elem_id: str, attrs: dict[str, AttrValueType], req: Request = INJECT) -> None:
        """Add multiple attributes to an element."""
        return self.get_store(req).add_attrs(elem_id, attrs)

    @route("DELETE", "/elements/{elem_id}/attrs/{name}", tags=["tags"])
    def del_attr(self, elem_id: str, name: str, req: Request = INJECT) -> None:
        return self.get_store(req).del_attr(elem_id, name)

    @route("PUT", "/elements/{elem_id}/metrics/{name}", tags=["tags"])
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput, req: Request = INJECT) -> None:
        return self.get_store(req).add_metric(elem_id, name, metric_input)

    @route("DELETE", "/elements/{elem_id}/metrics/{name}", tags=["tags"])
    def del_metric(self, elem_id: str, name: str, req: Request = INJECT) -> None:
        return self.get_store(req).del_metric(elem_id, name)

    @route("POST", "/elements/{elem_id}/tagging", tags=["tags"])
    def tagging(self, elem_id: str, tagging_input: TaggingInput, req: Request = INJECT) -> None:
        return self.get_store(req).tagging(elem_id, tagging_input)

    @route("POST", "/batch/{elem_type}/tagging", tags=["tags"])
    def batch_tagging(self, elem_type: ElemType, inputs: list[ElementTagging], req: Request = INJECT) -> None:
        return self.get_store(req).batch_tagging(elem_type, inputs)

    @route("PUT", "/elements/{elem_id}/values/{key}", tags=["values"])
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput, req: Request = INJECT) -> Value:
        return self.get_store(req).insert_value(elem_id, key, value_input)

    @route("POST", "/elements/{target_id}/tasks", tags=["tasks"])
    def insert_task(self, target_id: str, task_input: TaskInput, req: Request = INJECT) -> Task:
        return self.get_store(req).insert_task(target_id, task_input)

    @route("POST", "/docs", tags=["docs"])
    def insert_doc(self, doc_input: DocInput, skip_ext_check: bool = False, req: Request = INJECT) -> Doc:
        return self.get_store(req).insert_doc(doc_input, skip_ext_check)

    @route("POST", "/pages", tags=["pages"])
    def insert_page(self, page_input: PageInput, req: Request = INJECT) -> Page:
        return self.get_store(req).insert_page(page_input)

    @route("PUT", "/pages/{page_id}/layouts/{provider}", tags=["layouts"])
    def insert_layout(
        self,
        page_id: str,
        provider: str,
        layout_input: LayoutInput,
        insert_blocks: bool = True,
        upsert: bool = False,
        req: Request = INJECT,
    ) -> Layout:
        return self.get_store(req).insert_layout(page_id, provider, layout_input, insert_blocks, upsert)

    @route("POST", "/pages/{page_id}/blocks", tags=["blocks"])
    def insert_block(self, page_id: str, block_input: BlockInput, req: Request = INJECT) -> Block:
        return self.get_store(req).insert_block(page_id, block_input)

    @route("POST", "/pages/{page_id}/blocks/batch", tags=["blocks"])
    def insert_blocks(self, page_id: str, blocks: list[BlockInput], req: Request = INJECT) -> list[Block]:
        return self.get_store(req).insert_blocks(page_id, blocks)

    @route("POST", "/blocks", tags=["blocks"])
    def insert_standalone_block(self, block_input: StandaloneBlockInput, req: Request = INJECT) -> Block:
        return self.get_store(req).insert_standalone_block(block_input)

    @route("PUT", "/blocks/{block_id}/contents/{version}", tags=["contents"])
    def insert_content(
        self, block_id: str, version: str, content_input: ContentInput, upsert: bool = False, req: Request = INJECT
    ) -> Content:
        return self.get_store(req).insert_content(block_id, version, content_input, upsert)

    @route("PUT", "/pages/{page_id}/content-blocks-layouts/{provider}", tags=["layouts"])
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
        req: Request = INJECT,
    ) -> Layout:
        return self.get_store(req).insert_content_blocks_layout(page_id, provider, content_blocks, upsert)

    @route("POST", "/evallayouts", tags=["evaluations"])
    def insert_eval_layout(
        self,
        layout_id: str,
        provider: str,
        blocks: list[EvalLayoutBlock] | None = None,
        relations: list[dict] | None = None,
        req: Request = INJECT,
    ):
        """Insert a new eval layout into the database."""
        return self.get_store(req).insert_eval_layout(layout_id, provider, blocks, relations)

    @route("POST", "/evalcontents", tags=["evaluations"])
    def insert_eval_content(
        self,
        content_id: str,
        version: str,
        format: str,
        content: str,
        req: Request = INJECT,
    ):
        """Insert a new eval content into the database."""
        return self.get_store(req).insert_eval_content(content_id, version, format, content)

    ###################
    # TASK OPERATIONS #
    ###################

    @route("POST", "/grab-new-tasks/{command}", tags=["tasks"])
    def grab_new_tasks(
        self,
        command: str,
        num: int = 10,
        hold_sec: int = 3600,
        args: dict[str, Any] = {},  # for backward compatibility
        req: Request = INJECT,
    ) -> list[Task]:
        return self.get_store(req).grab_new_tasks(command, num, hold_sec)

    @route("POST", "/update-grabbed-task/{task_id}", tags=["tasks"])
    def update_task(
        self,
        task_id: str,
        command: str,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
        task: Task | None = None,
        grab_time: int = 0,  # for backward compatibility
        req: Request = INJECT,
    ) -> None:
        return self.get_store(req).update_task(task_id, command, status, error_message, task)

    @route("GET", "/count-tasks", tags=["tasks"])
    def count_tasks(self, command: str | None = None, req: Request = INJECT) -> list[TaskCount]:
        """Count tasks grouped by priority and status."""
        return self.get_store(req).count_tasks(command)

    #########################
    # MANAGEMENT OPERATIONS #
    #########################

    @route("GET", "/users", tags=["users"])
    def list_users(self, req: Request = INJECT) -> list[User]:
        """List all users in the system."""
        return self.get_store(req).list_users()

    @route("GET", "/users/{name}", tags=["users"])
    def get_user(self, name: str, req: Request = INJECT) -> User:
        """Get a user by name."""
        return self.get_store(req).get_user(name)

    @route("POST", "/users", tags=["users"])
    def insert_user(self, user_input: UserInput, req: Request = INJECT) -> User:
        """Add a new user to the system."""
        return self.get_store(req).insert_user(user_input)

    @route("PUT", "/users/{name}", tags=["users"])
    def update_user(self, name: str, user_update: UserUpdate, req: Request = INJECT) -> User:
        """Update an existing user in the system."""
        return self.get_store(req).update_user(name, user_update)

    @route("GET", "/known-names", tags=["names"])
    def list_known_names(self, req: Request = INJECT) -> list[KnownName]:
        """List all known tag/attribute/metric names in the system."""
        return self.get_store(req).list_known_names()

    @route("POST", "/known-names", tags=["names"])
    def insert_known_name(self, known_name_input: KnownNameInput, req: Request = INJECT) -> KnownName:
        """Add a new known tag/attribute/metric name to the system."""
        return self.get_store(req).insert_known_name(known_name_input)

    @route("PUT", "/known-names/{name}", tags=["names"])
    def update_known_name(self, name: str, known_name_update: KnownNameUpdate, req: Request = INJECT) -> KnownName:
        """Update an existing known tag/attribute/metric name in the system."""
        return self.get_store(req).update_known_name(name, known_name_update)

    @route("PUT", "/known-names/{attr_name}/options/{option_name}", tags=["names"])
    def add_known_option(self, attr_name: str, option_name: str, option_input: KnownOptionInput, req: Request = INJECT) -> None:
        """Add/Update a new known option to a known attribute name."""
        return self.get_store(req).add_known_option(attr_name, option_name, option_input)

    @route("DELETE", "/known-names/{attr_name}/options/{option_name}", tags=["names"])
    def del_known_option(self, attr_name: str, option_name: str, req: Request = INJECT) -> None:
        """Delete a known option from a known attribute name."""
        return self.get_store(req).del_known_option(attr_name, option_name)

    @route("GET", "/embedding-models", tags=["names"])
    def list_embedding_models(self, req: Request = INJECT) -> list[EmbeddingModel]:
        """List all embedding models in the system."""
        return self.get_store(req).list_embedding_models()

    @route("GET", "/embedding-models/{name}", tags=["names"])
    def get_embedding_model(self, name: str, req: Request = INJECT) -> EmbeddingModel:
        """Get an embedding model by name."""
        return self.get_store(req).get_embedding_model(name)

    @route("POST", "/embedding-models", tags=["names"])
    def insert_embedding_model(self, embedding_model: EmbeddingModel, req: Request = INJECT) -> EmbeddingModel:
        """Insert a new embedding model to the system."""
        return self.get_store(req).insert_embedding_model(embedding_model)

    @route("PUT", "/embedding-models/{name}", tags=["names"])
    def update_embedding_model(self, name: str, update: EmbeddingModelUpdate, req: Request = INJECT) -> EmbeddingModel:
        """Update an existing embedding model in the system."""
        return self.get_store(req).update_embedding_model(name, update)

    @route("POST", "/batch/{elem_type}/add-embedding/{model}", tags=["embeddings"])
    def add_embeddings(
        self,
        elem_type: EmbeddableElemType,
        model: str,
        embeddings: list[EmbeddingInput],
        req: Request = INJECT,
    ) -> None:
        """Add embeddings to elements of same elem_type."""
        return self.get_store(req).add_embeddings(elem_type, model, embeddings)

    @route("POST", "/search/{elem_type}/by-embedding/{model}", tags=["embeddings"])
    def search_embeddings(
        self,
        elem_type: EmbeddableElemType,
        model: str,
        query: EmbeddingQuery,
        req: Request = INJECT,
    ) -> list[Embedding]:
        """Search embeddings for elements of same elem_type."""
        return self.get_store(req).search_embeddings(elem_type, model, query)

    @route("GET", "/triggers", tags=["triggers"])
    def list_triggers(self, req: Request = INJECT) -> list[Trigger]:
        """List all triggers in the system."""
        return self.get_store(req).list_triggers()

    @route("GET", "/triggers/{trigger_id}", tags=["triggers"])
    def get_trigger(self, trigger_id: str, req: Request = INJECT) -> Trigger:
        """Get a trigger by ID."""
        return self.get_store(req).get_trigger(trigger_id)

    @route("POST", "/triggers", tags=["triggers"])
    def insert_trigger(self, trigger_input: TriggerInput, req: Request = INJECT) -> Trigger:
        """Insert a new trigger to the system."""
        return self.get_store(req).insert_trigger(trigger_input)

    @route("PUT", "/triggers/{trigger_id}", tags=["triggers"])
    def update_trigger(self, trigger_id: str, trigger_input: TriggerInput, req: Request = INJECT) -> Trigger:
        """Update an existing trigger in the system."""
        return self.get_store(req).update_trigger(trigger_id, trigger_input)

    @route("DELETE", "/triggers/{trigger_id}", tags=["triggers"])
    def delete_trigger(self, trigger_id: str, req: Request = INJECT) -> None:
        """Delete a trigger from the system."""
        return self.get_store(req).delete_trigger(trigger_id)


def main():
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="DocStore HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--measure-time", action="store_true", help="Enable time measurement")
    parser.add_argument("--disable-events", action="store_true", help="Disable events")
    args = parser.parse_args()

    print("Starting DocStore HTTP Server...")

    doc_store = DocStore(
        measure_time=args.measure_time,
        disable_events=args.disable_events,
        decode_value=False,
    )

    doc_server = DocServer(doc_store)

    uvicorn.run(
        doc_server.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )


if __name__ == "__main__":
    main()
