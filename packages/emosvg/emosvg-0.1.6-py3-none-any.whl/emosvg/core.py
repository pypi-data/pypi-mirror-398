from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw
from PIL.ImageFont import ImageFont, FreeTypeFont, TransposedFont

from . import helper
from .helper import Node, NodeType

PILImage = Image.Image
FontT = ImageFont | FreeTypeFont | TransposedFont
ColorT = int | str | tuple[int, int, int] | tuple[int, int, int, int]

# Define the path to the resources directory
RESOURCE_DIR = Path(__file__).parent / "resources"
EMOJI_SVG_DIR = RESOURCE_DIR / "openmoji-svg-color"


def get_emoji_svg_path(emoji: str) -> Path | None:
    """
    Converts a unicode emoji string to the corresponding SVG file path.
    Example: "😀" -> ".../1F600.svg"
    """
    filename = "-".join(f"{ord(char):X}" for char in emoji) + ".svg"
    file_path = EMOJI_SVG_DIR / filename
    return file_path if file_path.exists() else None


def get_emoji_bytes(emoji: str, width: float, height: float) -> bytes | None:
    svg_file = get_emoji_svg_path(emoji)
    if svg_file is None:
        return None

    png_data: bytes | None = cairosvg.svg2png(
        url=str(svg_file), output_width=width, output_height=height
    )

    return png_data


def get_emoji_image(emoji: str, width: float, height: float) -> PILImage | None:
    png_data = get_emoji_bytes(emoji, width, height)

    if png_data is None:
        return None

    # Create PIL Image from bytes
    image = Image.open(BytesIO(png_data)).convert("RGBA")

    return image


def get_font_size(font: FontT) -> float:
    match font:
        case FreeTypeFont():
            return font.size
        case TransposedFont():
            return get_font_size(font.font)
        case ImageFont():
            raise ValueError("Not support ImageFont")


def get_font_height(font: FontT) -> int:
    match font:
        case FreeTypeFont():
            ascent, descent = font.getmetrics()
            return ascent + descent
        case TransposedFont():
            return get_font_height(font.font)
        case ImageFont():
            raise ValueError("Not support ImageFont")


def wrap_text(
    text: str | list[str],
    font: FontT,
    max_width: int,
) -> list[list[Node]]:
    """Wrap text with automatic line breaks and return list of node lists.

    Parameters
    ----------
    text : str
        The input text to wrap (can contain newlines and emojis)
    font : FontT
        The font to use for width calculation
    max_width : int
        Maximum allowed width per line

    Returns
    -------
    list[list[Node]]
        List of lines, each line is a list of nodes (text or emoji)
    """
    if not text:
        return []

    # First split by explicit newlines
    if isinstance(text, list):
        paragraphs = text
    else:
        paragraphs = text.splitlines()
    wrapped_lines: list[list[Node]] = []

    for paragraph in paragraphs:
        if not paragraph:
            # Empty paragraph, add empty line
            wrapped_lines.append([])
            continue

        # Parse the paragraph into nodes
        nodes = helper.parse_line(paragraph)
        current_line = []
        current_width = 0

        for node in nodes:
            if node.type is NodeType.EMOJI:
                node_width = int(get_font_size(font))  # Emoji width equals font size
            else:
                node_width = int(font.getlength(node.content))

            # If adding this node would exceed max width, start new line
            if current_width + node_width > max_width and current_line:
                wrapped_lines.append(current_line)
                current_line = [node]
                current_width = node_width
            else:
                current_line.append(node)
                current_width += node_width

        # Add the last line of the paragraph
        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines


def text_with_wrapped(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[list[Node]],
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    scale: float = 1.1,
) -> None:
    """Text rendering method with Unicode emoji.

    Parameters
    ----------
    image: PILImage
        The image to render onto
    xy: tuple[int, int]
        Rendering position (x, y)
    lines: list[str]
        The text lines to render
    font: FontT
        The font to use
    fill: ColorT | None
        Text color, defaults to black
    line_height: int | None
        Line height, defaults to font height
    scale: float
        Emoji scale factor, defaults to 1.1
    """
    if not lines:
        return

    x, y = xy
    draw = ImageDraw.Draw(image)
    line_height = line_height or get_font_height(font)

    # Collect needed emojis
    emj_set: set[str] = {
        node.content for nodes in lines for node in nodes if node.type is NodeType.EMOJI
    }

    # Calculate emoji size and position diff
    font_size = get_font_size(font)
    emj_size = font_size * scale
    x_diff = int((emj_size - font_size) / 2)
    y_diff = int((emj_size - line_height) / 2)

    # Get all pil images
    emj_map = {
        emj: get_emoji_image(
            emj,
            emj_size,
            emj_size,
        )
        for emj in emj_set
    }

    # Draw each line
    for line in lines:
        cur_x = x

        for node in line:
            if node.type is NodeType.EMOJI:
                if emj_img := emj_map.get(node.content):
                    image.paste(emj_img, (cur_x - x_diff, y - y_diff), emj_img)
                else:
                    # 忽略组合表情的修饰符，只渲染第一个字符
                    draw.text((cur_x, y), node.content[0], font=font, fill=fill)
                cur_x += int(font_size)
            else:
                draw.text((cur_x, y), node.content, font=font, fill=fill)
                cur_x += int(font.getlength(node.content))

        y += line_height


def text(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[str] | str,
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    scale: float = 1.1,
) -> None:
    """Text rendering method with Unicode emoji.

    Parameters
    ----------
    image: PILImage
        The image to render onto
    xy: tuple[int, int]
        Rendering position (x, y)
    lines: list[str]
        The text lines to render
    font: FontT
        The font to use
    fill: ColorT | None
        Text color, defaults to black
    line_height: int | None
        Line height, defaults to font height
    scale: float
        Emoji scale factor, defaults to 1.1
    """
    if not lines:
        return

    x, y = xy
    draw = ImageDraw.Draw(image)
    line_height = line_height or get_font_height(font)

    if isinstance(lines, str):
        lines = lines.splitlines()

    # Check if lines has emoji
    if not helper.contains_emoji(lines):
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        return

    # Parse lines into nodes
    wrapped_lines = helper.parse_lines(lines)

    text_with_wrapped(
        image,
        xy,
        wrapped_lines,
        font,
        fill=fill,
        line_height=line_height,
        scale=scale,
    )
