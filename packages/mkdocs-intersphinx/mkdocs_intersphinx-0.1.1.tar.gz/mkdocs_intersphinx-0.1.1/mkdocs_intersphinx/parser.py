"""Parse YAML frontmatter and HTML ref comments from markdown content."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class RefComment:
    """Represents a reference extracted from an HTML comment."""
    name: str
    line_number: int
    next_header_line: Optional[int] = None
    next_header_text: Optional[str] = None
    next_header_level: Optional[int] = None


@dataclass
class HeaderInfo:
    """Represents a markdown header."""
    text: str
    level: int
    line_number: int


def extract_html_ref_comments(markdown_content: str) -> List[RefComment]:
    """
    Extract HTML ref comments from markdown content.

    Looks for comments in the format: <!-- ref:reference-name -->

    Args:
        markdown_content: The markdown content to parse

    Returns:
        List of RefComment objects with reference names and line numbers
    """
    # Pattern matches: <!-- ref:reference-name --> with optional whitespace
    pattern = r'<!--\s*ref:([a-zA-Z0-9_-]+)\s*-->'

    lines = markdown_content.split('\n')
    ref_comments = []

    for line_num, line in enumerate(lines, start=1):
        matches = re.finditer(pattern, line)
        for match in matches:
            ref_name = match.group(1)
            ref_comments.append(RefComment(
                name=ref_name,
                line_number=line_num
            ))

    return ref_comments


def parse_markdown_headers(markdown_content: str) -> List[HeaderInfo]:
    """
    Parse markdown headers from content.

    Supports both ATX style (# Header) and Setext style (underlined).

    Args:
        markdown_content: The markdown content to parse

    Returns:
        List of HeaderInfo objects
    """
    lines = markdown_content.split('\n')
    headers = []

    # ATX style headers: # Header, ## Header, etc.
    atx_pattern = r'^(#{1,6})\s+(.+?)(?:\s*#*)?$'

    for line_num, line in enumerate(lines, start=1):
        # Check for ATX style headers
        match = re.match(atx_pattern, line.strip())
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headers.append(HeaderInfo(
                text=text,
                level=level,
                line_number=line_num
            ))

    return headers


def match_refs_to_headers(
    ref_comments: List[RefComment],
    headers: List[HeaderInfo]
) -> List[RefComment]:
    """
    Match HTML ref comments to the next header that appears after them.

    Args:
        ref_comments: List of ref comments to match
        headers: List of headers parsed from markdown

    Returns:
        Updated list of RefComment objects with header information filled in
    """
    for ref in ref_comments:
        # Find the first header that appears after this ref comment
        next_header = None
        for header in headers:
            if header.line_number > ref.line_number:
                next_header = header
                break

        if next_header:
            ref.next_header_line = next_header.line_number
            ref.next_header_text = next_header.text
            ref.next_header_level = next_header.level

    return ref_comments


def generate_anchor_id(header_text: str) -> str:
    """
    Generate an anchor ID from header text using MkDocs conventions.

    Follows the same rules as Python-Markdown's TOC extension:
    - Convert to lowercase
    - Replace spaces with hyphens
    - Remove or replace special characters
    - Remove leading/trailing hyphens

    Args:
        header_text: The header text to convert

    Returns:
        The anchor ID string
    """
    anchor = header_text.lower()
    anchor = re.sub(r'\s+', '-', anchor)
    # Keep only ASCII word characters and hyphens (removes non-ASCII characters)
    anchor = re.sub(r'[^a-z0-9_\-]', '', anchor)
    anchor = anchor.strip('-')
    anchor = re.sub(r'-+', '-', anchor)

    return anchor


def parse_page_for_refs(markdown_content: str) -> Tuple[List[RefComment], List[HeaderInfo]]:
    """
    Parse a markdown page for all ref comments and headers.

    This is a convenience function that combines extraction and matching.

    Args:
        markdown_content: The markdown content to parse

    Returns:
        Tuple of (matched ref_comments, all headers)
    """
    ref_comments = extract_html_ref_comments(markdown_content)
    headers = parse_markdown_headers(markdown_content)

    if ref_comments:
        ref_comments = match_refs_to_headers(ref_comments, headers)

    return ref_comments, headers
