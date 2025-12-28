from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    import pymupdf

_KNOWN_MKEYS = set(
    [
        "format",
        "title",
        "author",
        "subject",
        "keywords",
        "creator",
        "producer",
        "creationDate",
        "modDate",
        "trapped",
    ]
)


class PDFDocument:
    def __init__(self, pdf_bytes: bytes, dpi: int = 200):
        try:
            import pymupdf
        except ImportError as e:
            raise ImportError("pymupdf is required to use PDFDocument.") from e

        self._pymupdf = pymupdf

        self.pdf_bytes = pdf_bytes
        self.doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        self.num_pages = len(self.doc)
        self.dpi = dpi

    def __len__(self):
        return self.num_pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def page_width(self) -> float:
        """Return the width of the first page in points."""
        if self.num_pages > 0:
            return round(self.doc[0].rect.width, 2)
        return 0

    @property
    def page_height(self) -> float:
        """Return the height of the first page in points."""
        if self.num_pages > 0:
            return round(self.doc[0].rect.height, 2)
        return 0

    @property
    def metadata(self) -> dict[str, str]:
        """Return the metadata of the PDF document."""
        m = self.doc.metadata
        if not isinstance(m, dict):
            return {}
        return {k: v for k, v in m.items() if k in _KNOWN_MKEYS and v}

    def get_page(self, page_idx: int) -> "pymupdf.Page":
        if page_idx < 0 or page_idx >= self.num_pages:
            raise IndexError("Page number out of range")
        page = self.doc[page_idx]
        assert isinstance(page, self._pymupdf.Page)
        return page

    def get_pages(self) -> list["pymupdf.Page"]:
        return [self.doc[i] for i in range(self.num_pages)]

    def get_image(self, page_idx: int) -> Image.Image:
        page = self.get_page(page_idx)
        return self.page_to_image(page)

    def get_images(self) -> list[Image.Image]:
        return [self.page_to_image(page) for page in self.get_pages()]

    def page_to_image(self, page: "pymupdf.Page") -> Image.Image:
        mat = self._pymupdf.Matrix(self.dpi / 72, self.dpi / 72)
        pm = page.get_pixmap(matrix=mat, alpha=False)  # type: ignore
        return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)

    def get_text(self, min_length=16384, max_pages=20) -> str:
        text = ""
        for page_idx in range(self.num_pages):
            if len(text) >= min_length or page_idx >= max_pages:
                break
            if text[-1:] != "\n":
                text += "\n"
            page = self.get_page(page_idx)
            text += page.get_text("text")  # type: ignore
        return text

    def close(self):
        self.doc.close()


# def page_to_image(
#     page: PdfPage,
#     dpi: int = 144,  # changed from 200 to 144
#     max_width_or_height: int = 2560,  # changed from 4500 to 2560
# ) -> (Image.Image, float):
#     scale = dpi / 72
#
#     long_side_length = max(*page.get_size())
#     if long_side_length > max_width_or_height:
#         scale = max_width_or_height / long_side_length
#
#     bitmap: PdfBitmap = page.render(scale=scale)  # type: ignore
#     try:
#         image = bitmap.to_pil()
#     finally:
#         try:
#             bitmap.close()
#         except Exception:
#             pass
#     return image, scale
#
#
# def pdf_to_images(
#     pdf: str | bytes | PdfDocument,
#     dpi: int = 144,
#     max_width_or_height: int = 2560,
#     start_page_id: int = 0,
#     end_page_id: int | None = None,
# ) -> list[Image.Image]:
#     doc = pdf if isinstance(pdf, PdfDocument) else PdfDocument(pdf)
#     page_num = len(doc)
#
#     end_page_id = end_page_id if end_page_id is not None and end_page_id >= 0 else page_num - 1
#     if end_page_id > page_num - 1:
#         logger.warning("end_page_id is out of range, use images length")
#         end_page_id = page_num - 1
#
#     images = []
#     try:
#         for i in range(start_page_id, end_page_id + 1):
#             image, _ = page_to_image(doc[i], dpi, max_width_or_height)
#             images.append(image)
#     finally:
#         try:
#             doc.close()
#         except Exception:
#             pass
#     return images
