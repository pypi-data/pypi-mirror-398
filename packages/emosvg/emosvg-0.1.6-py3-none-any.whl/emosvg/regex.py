import re
from typing import Final

from .helper import EMOJI_SET, Node, NodeType

EMOJI_REGEX: Final[str] = "|".join(
    map(re.escape, sorted(EMOJI_SET, key=len, reverse=True))
)
EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(EMOJI_REGEX)


def parse_lines_by_regex(lines: list[str]) -> list[list[Node]]:
    return [parse_line_by_regex(line) for line in lines]


def parse_line_by_regex(line: str):
    nodes: list[Node] = []

    last_end = 0
    for mat in EMOJI_PATTERN.finditer(line):
        start, end = mat.span()

        if start > last_end:
            nodes.append(Node(NodeType.TEXT, line[last_end:start]))

        emoji_text = mat.group()
        nodes.append(Node(NodeType.EMOJI, emoji_text))
        last_end = end

    # Add remaining text after the last emoji
    if last_end < len(line):
        nodes.append(Node(NodeType.TEXT, line[last_end:]))

    return nodes
