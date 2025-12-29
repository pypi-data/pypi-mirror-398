"""Tests for parser module."""

import pytest
from mkdocs_intersphinx.parser import (
    extract_html_ref_comments,
    parse_markdown_headers,
    match_refs_to_headers,
    generate_anchor_id,
    parse_page_for_refs,
    RefComment,
    HeaderInfo,
)


class TestExtractHtmlRefComments:
    """Tests for extracting HTML ref comments."""

    def test_single_ref_comment(self):
        markdown = "<!-- ref:my-section -->\n## My Section"
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 1
        assert refs[0].name == "my-section"
        assert refs[0].line_number == 1

    def test_multiple_ref_comments(self):
        markdown = """
<!-- ref:section-one -->
## Section One

Some content

<!-- ref:section-two -->
## Section Two
"""
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 2
        assert refs[0].name == "section-one"
        assert refs[0].line_number == 2
        assert refs[1].name == "section-two"
        assert refs[1].line_number == 7

    def test_ref_with_various_whitespace(self):
        markdown = """
<!--ref:no-space-->
<!-- ref:one-space -->
<!--  ref:two-spaces  -->
"""
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 3
        assert refs[0].name == "no-space"
        assert refs[1].name == "one-space"
        assert refs[2].name == "two-spaces"

    def test_valid_ref_name_characters(self):
        markdown = """
<!-- ref:lowercase -->
<!-- ref:UPPERCASE -->
<!-- ref:with-hyphens -->
<!-- ref:with_underscores -->
<!-- ref:with123numbers -->
"""
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 5
        assert refs[0].name == "lowercase"
        assert refs[1].name == "UPPERCASE"
        assert refs[2].name == "with-hyphens"
        assert refs[3].name == "with_underscores"
        assert refs[4].name == "with123numbers"

    def test_no_ref_comments(self):
        markdown = """
# Just a header
Some content without refs
"""
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 0

    def test_regular_html_comments_ignored(self):
        markdown = """
<!-- This is a regular comment -->
<!-- Another comment: value -->
<!-- ref:this-should-match -->
"""
        refs = extract_html_ref_comments(markdown)

        assert len(refs) == 1
        assert refs[0].name == "this-should-match"


class TestParseMarkdownHeaders:
    """Tests for parsing markdown headers."""

    def test_atx_style_headers(self):
        markdown = """
# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
"""
        headers = parse_markdown_headers(markdown)

        assert len(headers) == 6
        assert headers[0].level == 1
        assert headers[0].text == "Level 1"
        assert headers[5].level == 6
        assert headers[5].text == "Level 6"

    def test_headers_with_trailing_hashes(self):
        markdown = """
# Header One #
## Header Two ##
### Header Three ###
"""
        headers = parse_markdown_headers(markdown)

        assert len(headers) == 3
        assert headers[0].text == "Header One"
        assert headers[1].text == "Header Two"
        assert headers[2].text == "Header Three"

    def test_headers_with_inline_code(self):
        markdown = """
# Header with `code`
## Another `inline.code()` example
"""
        headers = parse_markdown_headers(markdown)

        assert len(headers) == 2
        assert headers[0].text == "Header with `code`"
        assert headers[1].text == "Another `inline.code()` example"

    def test_line_numbers(self):
        markdown = """
# First Header

Some content

## Second Header
"""
        headers = parse_markdown_headers(markdown)

        assert len(headers) == 2
        assert headers[0].line_number == 2
        assert headers[1].line_number == 6

    def test_no_headers(self):
        markdown = "Just plain text without headers"
        headers = parse_markdown_headers(markdown)

        assert len(headers) == 0


class TestMatchRefsToHeaders:
    """Tests for matching refs to headers."""

    def test_match_single_ref_to_header(self):
        refs = [RefComment(name="my-ref", line_number=1)]
        headers = [HeaderInfo(text="My Header", level=2, line_number=2)]

        matched = match_refs_to_headers(refs, headers)

        assert len(matched) == 1
        assert matched[0].next_header_text == "My Header"
        assert matched[0].next_header_level == 2
        assert matched[0].next_header_line == 2

    def test_match_multiple_refs(self):
        refs = [
            RefComment(name="ref1", line_number=1),
            RefComment(name="ref2", line_number=5),
        ]
        headers = [
            HeaderInfo(text="Header 1", level=2, line_number=2),
            HeaderInfo(text="Header 2", level=2, line_number=6),
        ]

        matched = match_refs_to_headers(refs, headers)

        assert len(matched) == 2
        assert matched[0].next_header_text == "Header 1"
        assert matched[1].next_header_text == "Header 2"

    def test_ref_without_following_header(self):
        refs = [RefComment(name="orphan-ref", line_number=10)]
        headers = [HeaderInfo(text="Header", level=2, line_number=2)]

        matched = match_refs_to_headers(refs, headers)

        assert len(matched) == 1
        assert matched[0].next_header_text is None
        assert matched[0].next_header_line is None

    def test_multiple_refs_before_same_header(self):
        refs = [
            RefComment(name="ref1", line_number=1),
            RefComment(name="ref2", line_number=2),
        ]
        headers = [HeaderInfo(text="Header", level=2, line_number=3)]

        matched = match_refs_to_headers(refs, headers)

        # Both refs should match to the same header
        assert len(matched) == 2
        assert matched[0].next_header_text == "Header"
        assert matched[1].next_header_text == "Header"


class TestGenerateAnchorId:
    """Tests for generating anchor IDs."""

    def test_simple_header(self):
        assert generate_anchor_id("Simple Header") == "simple-header"

    def test_with_special_characters(self):
        assert generate_anchor_id("Header with Special!@#$%^&*()") == "header-with-special"

    def test_with_numbers(self):
        assert generate_anchor_id("Section 1.2.3") == "section-123"

    def test_with_code(self):
        # Backticks should be removed
        assert generate_anchor_id("Header with `code`") == "header-with-code"

    def test_multiple_spaces(self):
        assert generate_anchor_id("Multiple   Spaces   Header") == "multiple-spaces-header"

    def test_leading_trailing_hyphens(self):
        assert generate_anchor_id("  Header  ") == "header"
        assert generate_anchor_id("- Header -") == "header"

    def test_already_lowercase_with_hyphens(self):
        assert generate_anchor_id("already-formatted") == "already-formatted"

    def test_unicode_characters(self):
        # Unicode should be preserved
        result = generate_anchor_id("Héllo Wörld")
        assert result == "hllo-wrld"  # Non-ASCII stripped in our simple implementation


class TestParsePageForRefs:
    """Tests for the combined parsing function."""

    def test_full_page_parsing(self):
        markdown = """
---
title: My Page
---

# Main Title

<!-- ref:introduction -->
## Introduction

Some intro text.

<!-- ref:details -->
### Details Section

More content here.
"""
        refs, headers = parse_page_for_refs(markdown)

        assert len(refs) == 2
        assert len(headers) == 3

        # Check that refs are matched to headers
        assert refs[0].name == "introduction"
        assert refs[0].next_header_text == "Introduction"
        assert refs[0].next_header_level == 2

        assert refs[1].name == "details"
        assert refs[1].next_header_text == "Details Section"
        assert refs[1].next_header_level == 3

    def test_page_without_refs(self):
        markdown = """
# Just Headers

## No Refs Here

Regular content.
"""
        refs, headers = parse_page_for_refs(markdown)

        assert len(refs) == 0
        assert len(headers) == 2

    def test_page_without_headers(self):
        markdown = """
Just content without headers.

<!-- ref:orphan -->

This ref has no header to match.
"""
        refs, headers = parse_page_for_refs(markdown)

        assert len(refs) == 1
        assert len(headers) == 0
        assert refs[0].next_header_text is None
