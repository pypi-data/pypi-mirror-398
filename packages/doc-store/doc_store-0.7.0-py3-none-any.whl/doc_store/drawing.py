import os
import typing

from PIL import Image, ImageDraw, ImageFont
from PIL import __version__ as PILLOW_VERSION

if typing.TYPE_CHECKING:
    from .interface import Block, MaskBlock


FONT_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "drawing_font.ttf",
)

COLOR_MAPPING = {
    "title": ((31, 119, 180), (255, 255, 255)),  # dark blue
    "text": ((174, 199, 232), (20, 14, 53)),  # light blue
    "table": ((44, 160, 44), (255, 255, 255)),  # dark green
    "table_caption": ((0, 255, 0), (20, 14, 53)),  # green
    "table_footnote": ((152, 223, 138), (20, 14, 53)),  # light green
    "image": ((188, 189, 34), (255, 255, 255)),  # dark yellow
    "image_caption": ((255, 255, 0), (20, 14, 53)),  # yellow
    "image_footnote": ((219, 219, 141), (20, 14, 53)),  # light yellow
    "equation": ((197, 176, 213), (20, 14, 53)),  # light purple
    "equation_block": ((148, 103, 189), (255, 255, 255)),  # purple
    "code": ((23, 190, 207), (255, 255, 255)),  # dark cyan
    "code_caption": ((0, 255, 255), (20, 14, 53)),  # cyan
    "phonetic": ((227, 119, 194), (255, 255, 255)),  # pink
    "algorithm": ((255, 192, 0), (255, 255, 255)),  # orange
    "ref_text": ((255, 187, 120), (20, 14, 53)),  # light orange
    "list": ((247, 182, 210), (20, 14, 53)),  # light pink
    "page_number": ((165, 42, 42), (255, 255, 255)),  # red brown
    "header": ((139, 69, 19), (255, 255, 255)),  # brown
    "footer": ((140, 86, 75), (255, 255, 255)),  # brown gray
    "aside_text": ((153, 34, 144), (255, 255, 255)),  # apple purple
    "page_footnote": ((127, 127, 127), (255, 255, 255)),  # gray
    # ------------------------------------------------------------ #
    "page_title": ((0, 0, 255), (255, 255, 255)),  # blue
    "toc": ((0, 128, 128), (255, 255, 255)),  # teal
    "abstract": ((0, 255, 127), (20, 14, 53)),  # spring green
    "equation_number": ((158, 218, 229), (20, 14, 53)),  # light cyan
    "ref_block": ((255, 147, 42), (255, 255, 255)),  # apple orange
    "list_item": ((255, 0, 255), (255, 255, 255)),  # magenta
    "chart": ((255, 69, 0), (255, 255, 255)),  # orange red
    "chart_caption": ((255, 0, 0), (255, 255, 255)),  # red
    "chart_footnote": ((255, 152, 150), (20, 14, 53)),  # light red
    "molecular": ((255, 0, 127), (255, 255, 255)),  # rose
    "reaction": ((127, 0, 255), (255, 255, 255)),  # deep purple
    "seal": ((60, 179, 113), (20, 14, 53)),  # medium sea green
    "qrcode": ((0, 191, 255), (20, 14, 53)),  # deep sky blue
    "barcode": ((135, 206, 250), (20, 14, 53)),  # light sky blue
    "common_caption": ((255, 228, 181), (20, 14, 53)),  # moccasin
    "common_footnote": ((255, 250, 205), (20, 14, 53)),  # lemon chiffon
    "abandon": ((128, 128, 0), (255, 255, 255)),  # olive
    "unknown": ((128, 0, 0), (255, 255, 255)),  # maroon
    # ------------------------------------------------------------ #
    "header_image": ((189, 183, 107), (20, 14, 53)),  # dark khaki
    "footer_image": ((189, 183, 107), (20, 14, 53)),  # dark khaki
    "image_block": ((184, 134, 11), (20, 14, 53)),  # dark golden rod
    "equation_inline": ((123, 104, 238), (255, 255, 255)),  # medium slate blue
    "vertical_text": ((100, 149, 237), (20, 14, 53)),  # cornflower blue
    # ------------------------------------------------------------ #
    "_unused_1": ((0, 0, 128), (255, 255, 255)),  # navy
    "_unused_2": ((75, 0, 130), (255, 255, 255)),  # indigo
    "_unused_3": ((192, 192, 192), (20, 14, 53)),  # silver
    "_unused_4": ((107, 142, 35), (255, 255, 255)),  # olive drab
    "_unused_5": ((173, 255, 47), (20, 14, 53)),  # green yellow
}

ANGLE_SIGN_MAPPING = {
    0: "↑",
    90: "→",
    180: "↓",
    270: "←",
}


def draw_layout_blocks(
    image: Image.Image,
    blocks: list[dict] | list["Block"],
    show_label=True,
    show_index=True,
    show_type=True,
    show_angle=True,
    show_score=True,
) -> Image.Image:
    width, height = image.size
    font_size = int(min(width, height) * 0.018) + 2
    thickness = int(max(width, height) * 0.002)
    show_label = show_label and (show_index or show_type or show_angle or show_score)

    image = image.copy()
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_FILE_PATH, font_size, encoding="utf-8")

    for idx, block in enumerate(blocks):
        block_type = str(block["type"])
        if block_type == "super":
            continue

        color, font_color = COLOR_MAPPING.get(block_type) or COLOR_MAPPING["unknown"]

        # draw bbox
        x1, y1, x2, y2 = block["bbox"]
        x1 = x1 * width
        y1 = y1 * height
        x2 = x2 * width
        y2 = y2 * height
        rectangle = [(x1, y1), (x1, y2), (x2, y2), (x2, y1), (x1, y1)]
        draw.line(rectangle, width=thickness, fill=color)

        # prepare label
        if not show_label:
            continue
        label = f"{idx+1}" if show_index else ""
        if show_type:
            label = f"{label}.{block_type}" if label else block_type
        if show_angle and block.get("angle") in ANGLE_SIGN_MAPPING:
            label = f"{label}【{ANGLE_SIGN_MAPPING[block['angle']]}】"
        if show_score and block.get("score") is not None:
            label = f"{label} {block['score']:.2f}" if label else f"{block['score']:.2f}"
        if not label:
            continue

        # draw label
        if tuple(map(int, PILLOW_VERSION.split("."))) <= (10, 0, 0):
            tw, th = draw.textsize(label, font=font)  # type: ignore
        else:
            left, top, right, bottom = draw.textbbox((0, 0), label, font)
            tw, th = right - left, bottom - top + 4

        if y1 < th:
            draw.rectangle([(x1, y1), (x1 + tw + 4, y1 + th + 1)], fill=color)
            draw.text((x1 + 2, y1 - 2), label, fill=font_color, font=font)
        else:
            draw.rectangle([(x1, y1 - th), (x1 + tw + 4, y1 + 1)], fill=color)
            draw.text((x1 + 2, y1 - th - 2), label, fill=font_color, font=font)

    return image


def draw_mask_blocks(
    image: Image.Image,
    blocks: list[dict] | list["MaskBlock"],
) -> Image.Image:
    width, height = image.size

    image = image.copy()
    draw = ImageDraw.Draw(image)

    for idx, block in enumerate(blocks):
        # draw mask bbox
        x1, y1, x2, y2 = block["bbox"]
        x1 = x1 * width
        y1 = y1 * height
        x2 = x2 * width
        y2 = y2 * height
        rectangle = [(x1, y1), (x2, y2)]
        draw.rectangle(rectangle, fill=(255, 255, 255))

    return image
