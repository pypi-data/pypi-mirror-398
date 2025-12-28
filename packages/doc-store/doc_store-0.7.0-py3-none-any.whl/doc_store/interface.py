import io
import time
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Callable, Iterable, Literal, TypeVar

from PIL import Image
from pydantic import BaseModel

from .drawing import draw_layout_blocks, draw_mask_blocks
from .io import read_file, read_image, upload_local_file
from .pdf_doc import PDFDocument
from .s3 import get_s3_presigned_url, head_s3_object, put_s3_object
from .utils import BlockingThreadPool, decode_ndarray, secs_to_readable


class InputModel(BaseModel):
    pass


class DictModel(BaseModel):
    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def get(self, key: str, default: Any | None = None):
        return self.__dict__.get(key, default)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


#########
# Input #
#########


AttrValueType = str | list[str] | int | bool


class AttrInput(InputModel):
    value: AttrValueType


MetricValueType = float | int


class MetricInput(InputModel):
    value: MetricValueType


# allow operating tags/attrs/metrics in one request
class TaggingInput(InputModel):
    tags: list[str] | None = None
    attrs: dict[str, AttrValueType] | None = None
    metrics: dict[str, MetricValueType] | None = None
    del_tags: list[str] | None = None
    del_attrs: list[str] | None = None
    del_metrics: list[str] | None = None


class ElementTagging(TaggingInput):
    elem_id: str


EmbeddingVectorType = list[float]


class EmbeddingInput(InputModel):
    elem_id: str
    vector: EmbeddingVectorType


class EmbeddingQuery(InputModel):
    vector: EmbeddingVectorType
    k: int
    show_vector: bool = False


class ValueInput(InputModel):
    value: Any
    type: str | None = None


class TaskInput(InputModel):
    command: str
    args: dict[str, Any] | None = None
    priority: int = 0
    batch_id: str | None = None


class DocInput(InputModel):
    pdf_path: str
    pdf_filename: str | None = None
    orig_path: str | None = None
    orig_filename: str | None = None
    tags: list[str] | None = None


class PageInput(InputModel):
    image_path: str
    image_dpi: int | None = None
    doc_id: str | None = None
    page_idx: int | None = None
    tags: list[str] | None = None


class DocPageInput(InputModel):
    image_path: str
    image_dpi: int | None = None
    tags: list[str] | None = None


class MaskBlock(InputModel, DictModel):
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    attrs: dict[str, Any] | None = None


class BlockInput(InputModel):
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    score: float | None = None
    tags: list[str] | None = None


class StandaloneBlockInput(InputModel):
    type: str
    image_path: str
    tags: list[str] | None = None


class ContentBlockInput(BlockInput):
    format: str | None = None
    content: str | None = None
    content_tags: list[str] | None = None


class LayoutInput(InputModel):
    blocks: list[ContentBlockInput]
    masks: list[MaskBlock] = []
    relations: list[dict] | None = None
    is_human_label: bool = False
    tags: list[str] | None = None


class ContentInput(InputModel):
    format: str
    content: str
    is_human_label: bool = False
    tags: list[str] | None = None


class TriggerCondition(BaseModel):
    elem_type: Literal["doc", "page", "layout", "block", "content"]
    event_type: Literal["insert", "add_tag", "del_tag", "add_provider", "add_version"]
    event_user: str | None = None
    page_providers: list[str] | None = None  # Match page with all these providers
    layout_provider: list[str] | None = None  # Match layout with any of these providers
    block_type: list[str] | None = None  # Match block with any of these types
    block_versions: list[str] | None = None  # Match block with all these versions
    content_version: list[str] | None = None  # Match content with any of these versions
    tags: list[str] | None = None  # Match element with all these tags
    tag_added: list[str] | None = None  # Match add_tag event with any of these tags added
    tag_deleted: list[str] | None = None  # Match del_tag event with any of these tags deleted


class TriggerAction(BaseModel):
    action_type: Literal["add_tag", "insert_task"]
    add_tag: str | None = None  # Tag to add
    insert_task: TaskInput | None = None  # Task to insert


class TriggerInput(InputModel):
    name: str
    description: str
    condition: TriggerCondition
    actions: list[TriggerAction]


class Trigger(TriggerInput):
    id: str
    create_user: str
    create_time: int
    update_time: int


##########
# Output #
##########


class Element(DictModel):
    """Base class for all elements."""

    id: str
    rid: int
    create_time: int | None = None
    update_time: int | None = None
    _store: "DocStoreInterface | None" = None

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        state.pop("_store", None)
        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)

    @property
    def store(self) -> "DocStoreInterface":
        """Get the store associated with this element."""
        if not self._store:
            raise ValueError("Element does not have a store.")
        return self._store

    @store.setter
    def store(self, store: "DocStoreInterface") -> None:
        """Set the store for this element."""
        if not isinstance(store, DocStoreInterface):
            raise TypeError("store must be an instance of DocStoreInterface.")
        self._store = store


class DocElement(Element):
    """Base class for all doc elements."""

    tags: list[str] = []
    attrs: dict[str, AttrValueType] = {}
    metrics: dict[str, MetricValueType] = {}

    def add_tag(self, tag: str) -> None:
        """Add tag to an element."""
        self.store.add_tag(self.id, tag)
        if tag not in self.tags:
            self.tags = self.tags + [tag]

    def del_tag(self, tag: str) -> None:
        """Delete tag from an element."""
        self.store.del_tag(self.id, tag)
        if tag in self.tags:
            self.tags = [t for t in self.tags if t != tag]

    def add_attr(self, name: str, attr_input: AttrInput) -> None:
        """Add attribute to an element."""
        self.store.add_attr(self.id, name, attr_input)
        self.attrs = {**self.attrs, name: attr_input.value}

    def add_attrs(self, attrs: dict[str, AttrValueType]) -> None:
        """Add multiple attributes to an element."""
        self.store.add_attrs(self.id, attrs)
        self.attrs = {**self.attrs, **attrs}

    def del_attr(self, name: str) -> None:
        """Delete attribute from an element."""
        self.store.del_attr(self.id, name)
        self.attrs = {k: v for k, v in self.attrs.items() if k != name}

    def add_metric(self, name: str, metric_input: MetricInput) -> None:
        """Add metric to an element."""
        self.store.add_metric(self.id, name, metric_input)
        self.metrics = {**self.metrics, name: metric_input.value}

    def del_metric(self, name: str) -> None:
        """Delete metric from an element."""
        self.store.del_metric(self.id, name)
        self.metrics = {k: v for k, v in self.metrics.items() if k != name}

    def tagging(self, tagging_input: TaggingInput) -> None:
        """Add/Delete tags, attributes, and metrics to/from an element."""
        self.store.tagging(self.id, tagging_input)
        for tag in tagging_input.tags or []:
            if tag not in self.tags:
                self.tags = self.tags + [tag]
        if tagging_input.del_tags:
            self.tags = [t for t in self.tags if t not in tagging_input.del_tags]
        if tagging_input.attrs:
            self.attrs = {**self.attrs, **tagging_input.attrs}
        if tagging_input.del_attrs:
            self.attrs = {k: v for k, v in self.attrs.items() if k not in tagging_input.del_attrs}
        if tagging_input.metrics:
            self.metrics = {**self.metrics, **tagging_input.metrics}
        if tagging_input.del_metrics:
            self.metrics = {k: v for k, v in self.metrics.items() if k not in tagging_input.del_metrics}

    def try_get_value(self, key: str) -> "Value | None":
        """Try to get a value by key."""
        return self.store.try_get_value_by_elem_id_and_key(self.id, key)

    def get_value(self, key: str) -> "Value":
        """Get a value by key."""
        return self.store.get_value_by_elem_id_and_key(self.id, key)

    def find_values(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Value"]:
        """Find all values of the element."""
        return self.store.find_values(
            query=query,
            elem_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_value(self, key: str, value_input: ValueInput) -> "Value":
        """Insert a value for the element."""
        return self.store.insert_value(self.id, key, value_input)

    def list_tasks(
        self,
        query: dict | None = None,
        batch_id: str | None = None,
        command: str | None = None,
        status: str | None = None,
        create_user: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list["Task"]:
        """List tasks of the element by filters."""
        return self.store.list_tasks(
            query=query,
            target=self.id,
            batch_id=batch_id,
            command=command,
            status=status,
            create_user=create_user,
            skip=skip,
            limit=limit,
        )

    def insert_task(self, task_input: TaskInput) -> "Task":
        """Insert a task for the element."""
        return self.store.insert_task(self.id, task_input)


class Doc(DocElement):
    """Doc in the store."""

    pdf_path: str
    pdf_filename: str | None = None
    pdf_filesize: int
    pdf_hash: str
    num_pages: int
    page_width: float
    page_height: float
    metadata: dict = {}

    # Original file info (if exists)
    orig_path: str | None = None
    orig_filesize: int | None = None
    orig_filename: str | None = None
    orig_hash: str | None = None

    @property
    def pdf_bytes(self) -> bytes:
        """Get the PDF bytes of the doc."""
        return read_file(self.pdf_path)

    @property
    def pdf(self) -> PDFDocument:
        """Get the PDF document associated with the doc."""
        return PDFDocument(self.pdf_bytes)

    @property
    def pages(self) -> list["Page"]:
        """Get all pages of the doc."""
        pages = list(self.find_pages())
        pages.sort(key=lambda p: p.page_idx or 0)
        return pages

    def find_pages(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Page"]:
        """List pages of the doc by filters."""
        return self.store.find_pages(
            query=query,
            doc_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_page(self, page_idx: int, page_input: DocPageInput) -> "Page":
        """Insert a page for the doc, return the inserted page."""
        return self.store.insert_page(
            PageInput(
                image_path=page_input.image_path,
                image_dpi=page_input.image_dpi,
                doc_id=self.id,
                page_idx=page_idx,
                tags=page_input.tags,
            )
        )


class Page(DocElement):
    """Page of a doc."""

    doc_id: str | None = None
    page_idx: int | None = None
    image_path: str
    image_filesize: int
    image_hash: str
    image_width: int
    image_height: int
    image_dpi: int | None = None

    providers: list[str] = []

    # image_path before moving to S3
    old_image_path: str | None = None

    @property
    def image_bytes(self) -> bytes:
        """Get the image bytes of the page."""
        return read_file(self.image_path)

    @property
    def image(self) -> Image.Image:
        """Get the image of the page."""
        return read_image(self.image_path)

    @property
    def image_presigned_link(self) -> str:
        """Get the presigned link of the page image."""
        image_ext = self.image_path.split(".")[-1].lower()
        if image_ext in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif image_ext in ["png"]:
            mime_type = "image/png"
        elif image_ext in ["webp"]:
            mime_type = "image/webp"
        else:
            raise ValueError(f"Unsupported image format: {image_ext}.")
        return get_s3_presigned_url(self.image_path, expires_in=86400, content_type=mime_type)

    @property
    def image_pub_link(self) -> str:
        """Get the public link of the page image."""
        image_ext = self.image_path.split(".")[-1].lower()
        if image_ext in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif image_ext in ["png"]:
            mime_type = "image/png"
        elif image_ext in ["webp"]:
            mime_type = "image/webp"
        else:
            raise ValueError(f"Unsupported image format: {image_ext}.")

        pub_path = f"ddp-pages/{self.id}.{image_ext}"
        pub_s3_path = f"s3://pub-link/{pub_path}"
        pub_link_url = f"https://pub-link.shlab.tech/{pub_path}"

        if not head_s3_object(pub_s3_path):
            put_s3_object(pub_s3_path, self.image_bytes, ContentType=mime_type)
        return pub_link_url

    @property
    def super_block(self) -> "Block":
        """Get the super block of the page."""
        return self.store.get_super_block(self.id)

    @property
    def doc(self) -> Doc | None:
        """Get the doc associated with the page."""
        return self.store.get_doc(self.doc_id) if self.doc_id else None

    def try_get_layout(self, provider: str, expand: bool = False) -> "Layout | None":
        """Try to get the layout of the page by provider."""
        return self.store.try_get_layout_by_page_id_and_provider(self.id, provider, expand)

    def get_layout(self, provider: str, expand: bool = False) -> "Layout":
        """Get the layout of the page by provider."""
        return self.store.get_layout_by_page_id_and_provider(self.id, provider, expand)

    def find_layouts(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Layout"]:
        """List layouts of the page by filters."""
        return self.store.find_layouts(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def find_blocks(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Block"]:
        """List blocks of the page by filters."""
        return self.store.find_blocks(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def find_contents(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Content"]:
        """List contents of the page by filters."""
        return self.store.find_contents(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_layout(self, provider: str, layout_input: LayoutInput, insert_blocks=False, upsert=False) -> "Layout":
        """Insert a layout for the page, return the inserted layout."""
        return self.store.insert_layout(self.id, provider, layout_input, insert_blocks, upsert)

    def upsert_layout(self, provider: str, layout_input: LayoutInput, insert_blocks=False) -> "Layout":
        """Upsert a layout for the page, return the inserted or updated layout."""
        return self.store.upsert_layout(self.id, provider, layout_input, insert_blocks)

    def insert_block(self, block_input: BlockInput) -> "Block":
        """Insert a block for the page, return the inserted block."""
        return self.store.insert_block(self.id, block_input)

    def insert_blocks(self, blocks: list[BlockInput]) -> list["Block"]:
        """Insert multiple blocks for the page, return the inserted blocks."""
        return self.store.insert_blocks(self.id, blocks)

    def insert_content_blocks_layout(
        self,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> "Layout":
        """Insert a layout with content blocks for the page."""
        return self.store.insert_content_blocks_layout(
            self.id,
            provider,
            content_blocks,
            upsert,
        )


class Layout(DocElement):
    """Layout of a page, containing blocks and relations."""

    page_id: str
    provider: str
    masks: list[MaskBlock] = []
    blocks: list["Block"] = []
    relations: list[dict] = []
    contents: list["Content"] = []
    is_human_label: bool = False

    @property
    def page(self) -> Page:
        """Get the page associated with the layout."""
        return self.store.get_page(self.page_id)

    @property
    def masked_image(self) -> Image.Image:
        """Get the masked image of the layout."""
        page_image = self.page.image
        return draw_mask_blocks(page_image, self.masks)

    @property
    def framed_image(self) -> Image.Image:
        """Get the framed image of the layout."""
        page_image = self.page.image
        return draw_layout_blocks(page_image, self.blocks)

    def list_versions(self) -> list[str]:
        """List all content versions of the layout."""
        block_ids = [block.id for block in self.blocks]
        if not block_ids:
            return []

        versions = set()
        query = {"block_id": {"$in": block_ids}}
        for content in self.store.find_contents(query=query):
            versions.add(content.version)
        return sorted(versions)

    def list_blocks(self) -> list["Block"]:
        """Get all blocks of the layout."""
        block_ids = [block.id for block in self.blocks]
        if not block_ids:
            return []
        blocks = [*self.blocks]
        indices = {b.id: idx for idx, b in enumerate(self.blocks)}
        for block in self.store.find_blocks(query={"id": {"$in": block_ids}}):
            block_idx = indices.get(block.id)
            if block_idx is not None:
                blocks[block_idx] = block
        return blocks

    def list_contents(self, version: str | None = None) -> list["Content"]:
        """Get all contents of the layout by version."""
        block_ids = [block.id for block in self.blocks]
        if not block_ids:
            return []
        if not version:
            version = self.provider
        contents = {}
        if version == self.provider:
            contents = {c.block_id: c for c in self.contents}
        query = {"block_id": {"$in": block_ids}, "version": version}
        for content in self.store.find_contents(query=query):
            contents[content.block_id] = content
        return [contents[bid] for bid in block_ids if bid in contents]

    def expand(self) -> "Layout":
        """Expand the layout by loading all blocks and contents."""
        self.blocks = self.list_blocks()
        self.contents = self.list_contents()
        return self


class Block(DocElement):
    """Block of a page, representing a specific area with a type."""

    layout_id: str | None = None
    provider: str | None = None

    page_id: str | None
    type: str
    bbox: list[float]  # [0, 0, 1, 1] for full page
    angle: Literal[None, 0, 90, 180, 270] = None
    score: float | None = None

    image_path: str | None = None
    image_filesize: int | None = None
    image_hash: str | None = None
    image_width: int | None = None
    image_height: int | None = None

    versions: list[str] = []

    @property
    def page(self) -> Page | None:
        """Get the page associated with the block."""
        if self.page_id is None:
            return None
        return self.store.get_page(self.page_id)

    @property
    def image(self) -> Image.Image:
        """Get the image of the block."""
        if self.image_path is not None:
            return read_image(self.image_path)

        page = self.page
        if page is None:
            raise ValueError("Block does not have a page or image_path.")

        bbox = self.bbox
        angle = self.angle
        image = page.image

        x1, y1, x2, y2 = bbox
        x1 = x1 * image.width
        y1 = y1 * image.height
        x2 = x2 * image.width
        y2 = y2 * image.height

        image = image.crop((x1, y1, x2, y2))
        if angle:
            image = image.rotate(angle, expand=True)
        return image

    @property
    def image_bytes(self) -> bytes:
        """Get the image bytes of the block."""
        if self.image_path is not None:
            return read_file(self.image_path)

        image = self.image
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            return output.getvalue()

    @property
    def image_pub_link(self) -> str:
        """Get the public link of the block image."""

        image_ext = "png"  # default to png
        if self.image_path is not None:
            image_ext = self.image_path.split(".")[-1].lower()

        if image_ext in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif image_ext in ["png"]:
            mime_type = "image/png"
        elif image_ext in ["webp"]:
            mime_type = "image/webp"
        else:
            raise ValueError(f"Unsupported image format: {image_ext}.")

        pub_path = f"ddp-blocks/{self.id}.{image_ext}"
        pub_s3_path = f"s3://pub-link/{pub_path}"
        pub_link_url = f"https://pub-link.shlab.tech/{pub_path}"

        if not head_s3_object(pub_s3_path):
            put_s3_object(pub_s3_path, self.image_bytes, ContentType=mime_type)
        return pub_link_url

    def try_get_content(self, version: str) -> "Content | None":
        """Try to get the content of the block by version."""
        return self.store.try_get_content_by_block_id_and_version(self.id, version)

    def get_content(self, version: str) -> "Content":
        """Get the content of the block by version."""
        return self.store.get_content_by_block_id_and_version(self.id, version)

    def find_contents(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Content"]:
        """List contents of the block by filters."""
        return self.store.find_contents(
            query=query,
            block_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_content(self, version: str, content_input: ContentInput, upsert=False) -> "Content":
        """Insert content for the block, return the inserted content."""
        return self.store.insert_content(self.id, version, content_input, upsert)

    def upsert_content(self, version: str, content_input: ContentInput) -> "Content":
        """Upsert content for the block, return the inserted or updated content."""
        return self.store.upsert_content(self.id, version, content_input)


class Content(DocElement):
    """Content of a block, representing the text or data within a block."""

    # layout_id: str | None = None
    # provider: str | None = None

    page_id: str | None
    block_id: str
    version: str
    format: str
    content: str
    is_human_label: bool = False

    @property
    def page(self) -> Page | None:
        """Get the page associated with this content."""
        if self.page_id is None:
            return None
        return self.store.get_page(self.page_id)

    @property
    def block(self) -> Block:
        """Get the block associated with this content."""
        return self.store.get_block(self.block_id)


class Embedding(DictModel):
    elem_id: str
    model: str
    vector: EmbeddingVectorType | None
    score: float | None = None


class Value(Element):
    elem_id: str
    key: str
    type: str
    value: Any

    @property
    def elem(self) -> DocElement:
        """Get the element associated with this value."""
        return self.store.get(self.elem_id)

    def decode(self) -> "Value":
        """Decode the value if it is encoded."""
        if self.type == "ndarray" and isinstance(self.value, str):
            self.value = decode_ndarray(self.value)
        return self


class Task(DictModel):
    id: str
    target: str
    batch_id: str
    command: str
    args: dict[str, Any]
    priority: int
    status: str
    create_user: str
    create_time: int
    update_user: str | None = None
    update_time: int | None = None
    error_message: str | None = None


class TaskCount(BaseModel):
    command: str
    priority: int
    total: int
    pending: int
    running: int
    completed: int
    # failed: int


class User(DictModel):
    name: str
    aliases: list[str] = []
    restricted: bool = False
    is_admin: bool = False


class UserInput(InputModel):
    name: str
    aliases: list[str] = []
    restricted: bool = False


class UserUpdate(InputModel):
    aliases: list[str] | None = None
    restricted: bool | None = None
    is_admin: bool | None = None


class KnownOption(DictModel):
    name: str
    display_name: str
    description: str


class KnownOptionInput(InputModel):
    display_name: str = ""
    description: str = ""


class KnownName(DictModel):
    "Definition of tag/attribute/metric name."

    name: str
    display_name: str = ""
    description: str = ""
    type: Literal["tag", "attr", "metric", "project_tag", "dataset_tag", "model_tag"] = "tag"
    value_type: Literal["null", "int", "float", "str", "list_str", "bool"] = "null"
    min_value: float = 0
    max_value: float = 0
    options: list[KnownOption] = []
    disabled: bool = False


class KnownNameInput(InputModel):
    name: str
    display_name: str = ""
    description: str = ""
    type: Literal["tag", "attr", "metric", "project_tag", "dataset_tag", "model_tag"] = "tag"
    value_type: Literal["null", "int", "float", "str", "list_str", "bool"] = "null"
    min_value: float = 0
    max_value: float = 0


class KnownNameUpdate(InputModel):
    display_name: str | None = None
    description: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    disabled: bool | None = None


class EmbeddingModel(DictModel):
    name: str
    display_name: str
    description: str
    dimension: int
    normalized: bool


class EmbeddingModelUpdate(InputModel):
    display_name: str
    description: str


class UnauthorizedError(Exception):
    pass


class NotFoundError(Exception):
    pass


class AlreadyExistsError(Exception):
    pass


class ElementNotFoundError(NotFoundError):
    pass


class ElementExistsError(AlreadyExistsError):
    pass


class DocExistsError(ElementExistsError):
    def __init__(self, message: str, pdf_path: str, pdf_hash: str | None):
        super().__init__(message)
        self.pdf_path = pdf_path
        self.pdf_hash = pdf_hash


class TaskMismatchError(Exception):
    pass


ElemType = Literal["doc", "page", "layout", "block", "content", "value"]
EmbeddableElemType = Literal["page", "block"]

T = TypeVar("T", bound=Doc | Page | Layout | Block | Content | Value)
Q = TypeVar("Q", bound=Doc | Page | Layout | Block | Content | Value)


def _cls_to_elem_type(cls: type[T] | type[Q]) -> ElemType:
    return cls.__name__.lower()  # type: ignore


class DocStoreInterface(ABC):
    def get(self, elem_id: str) -> DocElement:
        """Get a element by its ID."""
        if elem_id.startswith("doc-"):
            return self.get_doc(elem_id)
        if elem_id.startswith("page-"):
            return self.get_page(elem_id)
        if elem_id.startswith("layout-"):
            if ".block-" in elem_id:
                return self.get_block(elem_id)
            if ".content-" in elem_id:
                return self.get_content(elem_id)
            return self.get_layout(elem_id)
        if elem_id.startswith("block-"):
            return self.get_block(elem_id)
        if elem_id.startswith("content-"):
            return self.get_content(elem_id)
        if elem_id.startswith("evallayout-"):
            return self.get_eval_layout(elem_id)
        if elem_id.startswith("evalcontent-"):
            return self.get_eval_content(elem_id)
        # TODO: fallback to block for now.
        return self.get_block(elem_id)

    def try_get(self, elem_id: str) -> DocElement | None:
        """Try to get a element by its ID, return None if not found."""
        try:
            return self.get(elem_id)
        except ElementNotFoundError:
            return None

    def try_get_doc(self, doc_id: str) -> Doc | None:
        """Try to get a doc by its ID, return None if not found."""
        try:
            return self.get_doc(doc_id)
        except ElementNotFoundError:
            return None

    def try_get_doc_by_pdf_path(self, pdf_path: str) -> Doc | None:
        """Try to get a doc by its PDF path, return None if not found."""
        try:
            return self.get_doc_by_pdf_path(pdf_path)
        except ElementNotFoundError:
            return None

    def try_get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc | None:
        """Try to get a doc by its PDF sha256sum hex-string, return None if not found."""
        try:
            return self.get_doc_by_pdf_hash(pdf_hash)
        except ElementNotFoundError:
            return None

    def try_get_page(self, page_id: str) -> Page | None:
        """Try to get a page by its ID, return None if not found."""
        try:
            return self.get_page(page_id)
        except ElementNotFoundError:
            return None

    def try_get_page_by_image_path(self, image_path: str) -> Page | None:
        """Try to get a page by its image path, return None if not found."""
        try:
            return self.get_page_by_image_path(image_path)
        except ElementNotFoundError:
            return None

    def try_get_layout(self, layout_id: str, expand: bool = False) -> Layout | None:
        """Try to get a layout by its ID, return None if not found."""
        try:
            return self.get_layout(layout_id, expand)
        except ElementNotFoundError:
            return None

    def try_get_layout_by_page_id_and_provider(self, page_id: str, provider: str, expand: bool = False) -> Layout | None:
        """Try to get a layout by its page ID and provider, return None if not found."""
        try:
            return self.get_layout_by_page_id_and_provider(page_id, provider, expand)
        except ElementNotFoundError:
            return None

    def try_get_block(self, block_id: str) -> Block | None:
        """Try to get a block by its ID, return None if not found."""
        try:
            return self.get_block(block_id)
        except ElementNotFoundError:
            return None

    def try_get_block_by_image_path(self, image_path: str) -> Block | None:
        """Try to get a block by its image path, return None if not found."""
        try:
            return self.get_block_by_image_path(image_path)
        except ElementNotFoundError:
            return None

    def try_get_content(self, content_id: str) -> Content | None:
        """Try to get a content by its ID, return None if not found."""
        try:
            return self.get_content(content_id)
        except ElementNotFoundError:
            return None

    def try_get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content | None:
        """Try to get a content by its block ID and version, return None if not found."""
        try:
            return self.get_content_by_block_id_and_version(block_id, version)
        except ElementNotFoundError:
            return None

    def try_get_value(self, value_id: str) -> Value | None:
        """Try to get a value by its ID, return None if not found."""
        try:
            return self.get_value(value_id)
        except ElementNotFoundError:
            return None

    def try_get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value | None:
        """Try to get a value by its elem_id and key, return None if not found."""
        try:
            return self.get_value_by_elem_id_and_key(elem_id, key)
        except ElementNotFoundError:
            return None

    def try_get_user(self, name: str) -> User | None:
        """Try to get a user by its name, return None if not found."""
        try:
            return self.get_user(name)
        except NotFoundError:
            return None

    def doc_tags(self) -> list[str]:
        """Get all distinct tags for docs."""
        return self.distinct_values("doc", "tags")

    def page_tags(self) -> list[str]:
        """Get all distinct tags for pages."""
        return self.distinct_values("page", "tags")

    def page_providers(self) -> list[str]:
        """Get all distinct providers for pages."""
        return self.distinct_values("page", "providers")

    def layout_providers(self) -> list[str]:
        """Get all distinct layout providers."""
        return self.distinct_values("layout", "provider")

    def layout_tags(self) -> list[str]:
        """Get all distinct tags for layouts."""
        return self.distinct_values("layout", "tags")

    def block_tags(self) -> list[str]:
        """Get all distinct tags for blocks."""
        return self.distinct_values("block", "tags")

    def block_versions(self) -> list[str]:
        """Get all distinct versions for blocks."""
        return self.distinct_values("block", "versions")

    def content_versions(self) -> list[str]:
        """Get all distinct content versions."""
        return self.distinct_values("content", "version")

    def content_tags(self) -> list[str]:
        """Get all distinct tags for contents."""
        return self.distinct_values("content", "tags")

    def find_docs(
        self,
        query: dict | list[dict] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Doc]:
        """List docs by filters."""
        query = query or {}
        return self.find("doc", query, skip=skip, limit=limit)  # type: ignore

    def find_pages(
        self,
        query: dict | list[dict] | None = None,
        doc_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Page]:
        """List pages by filters."""
        query = query or {}
        if doc_id is not None:
            if not isinstance(query, dict):
                raise ValueError("doc_id filter cannot be used with pipeline query.")
            query["doc_id"] = doc_id
        return self.find("page", query, skip=skip, limit=limit)  # type: ignore

    def find_layouts(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Layout]:
        """List layouts by filters."""
        query = query or {}
        if page_id is not None:
            if not isinstance(query, dict):
                raise ValueError("page_id filter cannot be used with pipeline query.")
            query["page_id"] = page_id
        return self.find("layout", query, skip=skip, limit=limit)  # type: ignore

    def find_blocks(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Block]:
        """List blocks by filters."""
        query = query or {}
        if page_id is not None:
            if not isinstance(query, dict):
                raise ValueError("page_id filter cannot be used with pipeline query.")
            query["page_id"] = page_id
        return self.find("block", query, skip=skip, limit=limit)  # type: ignore

    def find_contents(
        self,
        query: dict | list[dict] | None = None,
        page_id: str | None = None,
        block_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Content]:
        """List contents by filters."""
        query = query or {}
        if page_id is not None:
            if not isinstance(query, dict):
                raise ValueError("page_id filter cannot be used with pipeline query.")
            query["page_id"] = page_id
        if block_id is not None:
            if not isinstance(query, dict):
                raise ValueError("block_id filter cannot be used with pipeline query.")
            query["block_id"] = block_id
        return self.find("content", query, skip=skip, limit=limit)  # type: ignore

    def find_values(
        self,
        query: dict | list[dict] | None = None,
        elem_id: str | None = None,
        key: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Value]:
        """List values by filters."""
        query = query or {}
        if elem_id is not None:
            if not isinstance(query, dict):
                raise ValueError("elem_id filter cannot be used with pipeline query.")
            query["elem_id"] = elem_id
        if key is not None:
            if not isinstance(query, dict):
                raise ValueError("key filter cannot be used with pipeline query.")
            query["key"] = key
        return self.find("value", query, skip=skip, limit=limit)  # type: ignore

    def insert_local_doc(self, local_pdf_path: str) -> Doc:
        s3_pdf_path = upload_local_file("doc", local_pdf_path)
        try:
            return self.insert_doc(DocInput(pdf_path=s3_pdf_path))
        except DocExistsError as e:
            return self.get_doc_by_pdf_hash(e.pdf_hash) if e.pdf_hash else self.get_doc_by_pdf_path(e.pdf_path)

    def insert_local_page(self, local_image_path: str) -> Page:
        s3_image_path = upload_local_file("page", local_image_path)
        try:
            return self.insert_page(PageInput(image_path=s3_image_path))
        except ElementExistsError:
            return self.get_page_by_image_path(s3_image_path)

    def insert_local_block(self, type: str, local_image_path: str) -> Block:
        s3_image_path = upload_local_file("block", local_image_path)
        try:
            return self.insert_standalone_block(StandaloneBlockInput(type=type, image_path=s3_image_path))
        except ElementExistsError:
            return self.get_block_by_image_path(s3_image_path)

    def upsert_layout(self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=False) -> Layout:
        """Upsert a layout for a page."""
        return self.insert_layout(page_id, provider, layout_input, insert_blocks, upsert=True)

    def upsert_content(self, block_id: str, version: str, content_input: ContentInput) -> Content:
        """Upsert content for a block."""
        return self.insert_content(block_id, version, content_input, upsert=True)

    def try_get_task(self, task_id: str) -> Task | None:
        """Try to get a task by its ID, return None if not found."""
        try:
            return self.get_task(task_id)
        except ElementNotFoundError:
            return None

    def grab_new_task(self, command: str, hold_sec=3600) -> Task | None:
        """Grab a new task for processing."""
        grabbed_tasks = self.grab_new_tasks(command=command, num=1, hold_sec=hold_sec)
        return grabbed_tasks[0] if grabbed_tasks else None

    def update_grabbed_task(
        self,
        task: Task,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
    ) -> None:
        """Update a task after processing."""
        send_task = (status == "error") or bool(task.batch_id)
        return self.update_task(
            task_id=task.id,
            command=task.command,
            status=status,
            error_message=error_message,
            task=task if send_task else None,
        )

    def iterate(
        self,
        elem_type: type[T],
        func: Callable[[int, T], None],
        query: dict | list[dict] | None = None,
        query_from: type[Q] | None = None,
        max_workers: int = 10,
        total: int | None = None,
    ) -> None:
        if query is None:
            query = {}

        if total is None:
            print("Estimating element count...")
            begin = time.time()
            cnt = self.count(
                elem_type=_cls_to_elem_type(elem_type),
                query=query,
                query_from=_cls_to_elem_type(query_from) if query_from else None,
                estimated=True,
            )
            elapsed = round(time.time() - begin, 2)
            print(f"Estimation done. Found {cnt} elements in {elapsed} seconds.")
        else:
            cnt = max(0, total)

        print("Iterating over elements...")
        begin = time.time()
        cursor = self.find(
            elem_type=_cls_to_elem_type(elem_type),
            query=query,
            query_from=_cls_to_elem_type(query_from) if query_from else None,
        )

        last_report_time = time.time()
        with BlockingThreadPool(max_workers) as executor:
            for idx, elem_data in enumerate(cursor):
                now = time.time()
                if idx > 0 and (now - last_report_time) > 10:
                    curr = str(idx).rjust(len(str(cnt)))
                    curr = f"{curr}/{cnt}" if cnt > 0 else curr
                    elapsed = round(now - begin, 2)
                    rps = round(idx / elapsed, 2) if elapsed > 0 else idx
                    message = f"Processed {curr} elements in {elapsed}s, {rps}r/s"
                    if cnt > 0:
                        prog = round(idx / cnt * 100, 2)
                        remaining_secs = int(elapsed * (cnt - idx) / idx)
                        rtime = secs_to_readable(remaining_secs)
                        message = f"[{prog:5.2f}%] {message}, remaining time: {rtime}"
                    print(message)
                    last_report_time = now
                executor.submit(func, idx, elem_data)
            executor.shutdown(wait=True)

    @abstractmethod
    def health_check(self, show_stats: bool = False) -> dict:
        """Check the health of the doc store."""
        raise NotImplementedError()

    @abstractmethod
    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        raise NotImplementedError()

    @abstractmethod
    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        raise NotImplementedError()

    @abstractmethod
    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        raise NotImplementedError()

    @abstractmethod
    def get_layout(self, layout_id: str, expand: bool = False) -> Layout:
        """Get a layout by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str, expand: bool = False) -> Layout:
        """Get a layout by its page ID and provider."""
        raise NotImplementedError()

    @abstractmethod
    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_block_by_image_path(self, image_path: str) -> Block:
        """Get a block by its image path."""
        raise NotImplementedError()

    @abstractmethod
    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        raise NotImplementedError()

    @abstractmethod
    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        raise NotImplementedError()

    @abstractmethod
    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its elem_id and key."""
        raise NotImplementedError()

    @abstractmethod
    def get_eval_layout(self, eval_layout_id: str) -> "EvalLayout":
        """Get an eval layout by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_eval_content(self, eval_content_id: str) -> "EvalContent":
        """Get an eval content by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "providers", "provider", "versions", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get all distinct values for a specific field of an element type."""
        raise NotImplementedError()

    @abstractmethod
    def find(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Element]:
        """Find elements of a specific type matching the query."""
        raise NotImplementedError()

    @abstractmethod
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        raise NotImplementedError()

    ####################
    # WRITE OPERATIONS #
    ####################

    @abstractmethod
    def add_tag(self, elem_id: str, tag: str) -> None:
        """Add tag to an element."""
        raise NotImplementedError()

    @abstractmethod
    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        raise NotImplementedError()

    @abstractmethod
    def batch_add_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch add tag to multiple elements."""
        raise NotImplementedError()

    @abstractmethod
    def batch_del_tag(self, elem_type: ElemType, tag: str, elem_ids: list[str]) -> None:
        """Batch delete tag from multiple elements."""
        raise NotImplementedError()

    @abstractmethod
    def add_attr(self, elem_id: str, name: str, attr_input: AttrInput) -> None:
        """Add an attribute to an element."""
        raise NotImplementedError()

    @abstractmethod
    def add_attrs(self, elem_id: str, attrs: dict[str, AttrValueType]) -> None:
        """Add multiple attributes to an element."""
        raise NotImplementedError()

    @abstractmethod
    def del_attr(self, elem_id: str, name: str) -> None:
        """Delete an attribute from an element."""
        raise NotImplementedError()

    @abstractmethod
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        raise NotImplementedError()

    @abstractmethod
    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        raise NotImplementedError()

    @abstractmethod
    def tagging(self, elem_id: str, tagging_input: TaggingInput) -> None:
        """Add/Delete tags, attributes, and metrics to/from an element."""
        raise NotImplementedError()

    @abstractmethod
    def batch_tagging(self, elem_type: ElemType, inputs: list[ElementTagging]) -> None:
        """Batch add/delete tags, attributes, and metrics to/from multiple elements."""
        raise NotImplementedError()

    @abstractmethod
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a element."""
        raise NotImplementedError()

    @abstractmethod
    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_layout(
        self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=False, upsert=False
    ) -> Layout:
        """Insert a new layout into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        raise NotImplementedError()

    @abstractmethod
    def insert_blocks(self, page_id: str, blocks: list[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        raise NotImplementedError()

    @abstractmethod
    def insert_standalone_block(self, block_input: StandaloneBlockInput) -> Block:
        """Insert a new standalone block (without page)."""
        raise NotImplementedError()

    @abstractmethod
    def insert_content(self, block_id: str, version: str, content_input: ContentInput, upsert=False) -> Content:
        """Insert a new content for a block."""
        raise NotImplementedError()

    @abstractmethod
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        raise NotImplementedError()

    @abstractmethod
    def insert_eval_layout(
        self,
        layout_id: str,
        provider: str,
        blocks: list["EvalLayoutBlock"] | None = None,
        relations: list[dict] | None = None,
    ) -> "EvalLayout":
        """Insert a new eval layout into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_eval_content(
        self,
        content_id: str,
        version: str,
        format: str,
        content: str,
    ) -> "EvalContent":
        """Insert a new eval content into the database."""
        raise NotImplementedError()

    ###################
    # TASK OPERATIONS #
    ###################

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task into the database."""
        raise NotImplementedError()

    @abstractmethod
    def grab_new_tasks(self, command: str, num=10, hold_sec=3600) -> list[Task]:
        """Grab new tasks for processing."""
        raise NotImplementedError()

    @abstractmethod
    def update_task(
        self,
        task_id: str,
        command: str,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
        task: Task | None = None,
    ) -> None:
        """Update a task after processing."""
        raise NotImplementedError()

    @abstractmethod
    def count_tasks(self, command: str | None = None) -> list[TaskCount]:
        """Count tasks grouped by priority and status."""
        raise NotImplementedError()

    #########################
    # MANAGEMENT OPERATIONS #
    #########################

    @abstractmethod
    def list_users(self) -> list[User]:
        """List all users in the system."""
        raise NotImplementedError()

    @abstractmethod
    def get_user(self, name: str) -> User:
        """Get a user by name."""
        raise NotImplementedError()

    @abstractmethod
    def insert_user(self, user_input: UserInput) -> User:
        """Add a new user to the system."""
        raise NotImplementedError()

    @abstractmethod
    def update_user(self, name: str, user_update: UserUpdate) -> User:
        """Update an existing user in the system."""
        raise NotImplementedError()

    @abstractmethod
    def list_known_names(self) -> list[KnownName]:
        """List all known tag/attribute/metric names in the system."""
        raise NotImplementedError()

    @abstractmethod
    def insert_known_name(self, known_name_input: KnownNameInput) -> KnownName:
        """Add a new known tag/attribute/metric name to the system."""
        raise NotImplementedError()

    @abstractmethod
    def update_known_name(self, name: str, known_name_update: KnownNameUpdate) -> KnownName:
        """Update an existing known tag/attribute/metric name in the system."""
        raise NotImplementedError()

    @abstractmethod
    def add_known_option(self, attr_name: str, option_name: str, option_input: KnownOptionInput) -> None:
        """Add/Update a new known option to a known attribute name."""
        raise NotImplementedError()

    @abstractmethod
    def del_known_option(self, attr_name: str, option_name: str) -> None:
        """Delete a known option from a known attribute name."""
        raise NotImplementedError()

    ####################
    # Embedding Models #
    ####################

    @abstractmethod
    def list_embedding_models(self) -> list[EmbeddingModel]:
        """List all embedding models in the system."""
        raise NotImplementedError()

    @abstractmethod
    def get_embedding_model(self, name: str) -> EmbeddingModel:
        """Get an embedding model by name."""
        raise NotImplementedError()

    @abstractmethod
    def insert_embedding_model(self, embedding_model: EmbeddingModel) -> EmbeddingModel:
        """Insert a new embedding model to the system."""
        raise NotImplementedError()

    @abstractmethod
    def update_embedding_model(self, name: str, update: EmbeddingModelUpdate) -> EmbeddingModel:
        """Update an existing embedding model in the system."""
        raise NotImplementedError()

    @abstractmethod
    def add_embeddings(self, elem_type: EmbeddableElemType, model: str, embeddings: list[EmbeddingInput]) -> None:
        """Add embeddings to elements of same elem_type."""
        raise NotImplementedError()

    @abstractmethod
    def search_embeddings(self, elem_type: EmbeddableElemType, model: str, query: EmbeddingQuery) -> list[Embedding]:
        """Search embeddings for elements of same elem_type."""
        raise NotImplementedError()

    ############
    # Triggers #
    ############

    @abstractmethod
    def list_triggers(self) -> list[Trigger]:
        """List all triggers in the system."""
        raise NotImplementedError()

    @abstractmethod
    def get_trigger(self, trigger_id: str) -> Trigger:
        """Get a trigger by ID."""
        raise NotImplementedError()

    @abstractmethod
    def insert_trigger(self, trigger_input: TriggerInput) -> Trigger:
        """Insert a new trigger to the system."""
        raise NotImplementedError()

    @abstractmethod
    def update_trigger(self, trigger_id: str, trigger_input: TriggerInput) -> Trigger:
        """Update an existing trigger in the system."""
        raise NotImplementedError()

    @abstractmethod
    def delete_trigger(self, trigger_id: str) -> None:
        """Delete a trigger from the system."""
        raise NotImplementedError()


class EvalLayoutBlock(InputModel):
    id: str
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    format: str
    content: str


class EvalStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class EvalLayout(DocElement):
    """Eval layout of a page."""

    layout_id: str  # gt layout_id
    provider: str  # eval target provider
    blocks: list[EvalLayoutBlock] = []
    relations: list[dict] = []
    status: EvalStatus = EvalStatus.PENDING


class EvalContent(DocElement):
    """Eval content of a block."""

    content_id: str  # gt content_id
    version: str  # eval target version
    format: str
    content: str
    status: EvalStatus = EvalStatus.PENDING
