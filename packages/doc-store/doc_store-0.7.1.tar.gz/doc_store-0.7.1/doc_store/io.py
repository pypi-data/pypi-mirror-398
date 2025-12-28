import hashlib
import io
import os
from functools import lru_cache
from typing import Literal

from PIL import Image, ImageDraw

from .s3 import head_s3_object, put_s3_object, read_s3_object_bytes

Image.MAX_IMAGE_PIXELS = None


_UPLOAD_DIRS = {
    "doc": "s3://doc-store/docs-by-hash/",
    "page": "s3://doc-store/pages-by-hash/",
    "block": "s3://doc-store/blocks-by-hash/",
}


@lru_cache
def read_file(file_path: str, allow_local=True) -> bytes:
    if file_path.startswith("s3://"):
        return read_s3_object_bytes(file_path)
    elif allow_local and os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            return f.read()
    raise ValueError(f"File {file_path} does not exist or is not accessible.")


def read_local_file(file_path: str) -> bytes:
    if not os.path.isfile(file_path):
        raise ValueError(f"Local file {file_path} does not exist.")
    with open(file_path, "rb") as f:
        return f.read()


def upload_local_file(file_type: Literal["doc", "page", "block"], file_path: str) -> str:
    file_ext = file_path.split(".")[-1].lower()
    if file_type == "doc" and file_ext != "pdf":
        raise ValueError("file_path must end with .pdf for doc type.")
    if file_type in ("page", "block") and file_ext not in ("jpg", "jpeg", "png", "webp"):
        raise ValueError("file_path must end with .jpg, .jpeg, .png, or .webp for page/block type.")
    file_bytes = read_local_file(file_path)
    if file_type == "doc":
        try_read_pdf(file_bytes)
    elif file_type in ("page", "block"):
        try_read_image(file_bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    upload_file_path = f"{_UPLOAD_DIRS[file_type]}{file_hash}.{file_ext}"
    if not head_s3_object(upload_file_path):
        put_s3_object(upload_file_path, file_bytes)
    return upload_file_path


def try_read_pdf(file_bytes: bytes) -> None:
    from .pdf_doc import PDFDocument

    if PDFDocument(file_bytes).num_pages <= 0:
        raise ValueError(f"PDF document has no pages.")


def try_read_image(file_bytes: bytes) -> None:
    image = Image.open(io.BytesIO(file_bytes))
    image.convert("RGB")  # Some broken image may raise.


def read_image(file_path: str) -> Image.Image:
    content = read_file(file_path)
    image = Image.open(io.BytesIO(content))
    try:
        return image.convert("RGB")
    except Exception:
        # image is broken, return fake image
        fake_size = [*image.size]
        fake_image = Image.new("RGB", fake_size, (255, 255, 255))
        draw = ImageDraw.Draw(fake_image)
        draw.line((0, 0, *fake_size), fill=(255, 0, 0), width=10)
        draw.line((0, fake_size[1], fake_size[0], 0), fill=(255, 0, 0), width=10)
        return fake_image
