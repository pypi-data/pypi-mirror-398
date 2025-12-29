"""Tests for inventory module."""

import pytest
from pathlib import Path
from mkdocs_intersphinx.inventory import (
    InventoryEntry,
    create_inventory,
    validate_inventory_entries,
)


class TestInventoryEntry:
    """Tests for InventoryEntry dataclass."""

    def test_valid_entry(self):
        entry = InventoryEntry(
            name="test-ref",
            domain="std",
            role="doc",
            priority=1,
            uri="page.html",
            display_name="Test Page"
        )

        assert entry.name == "test-ref"
        assert entry.domain == "std"
        assert entry.role == "doc"
        assert entry.priority == 1
        assert entry.uri == "page.html"
        assert entry.display_name == "Test Page"

    def test_entry_with_anchor(self):
        entry = InventoryEntry(
            name="section-ref",
            domain="std",
            role="label",
            priority=1,
            uri="page.html#section",
            display_name="Section Title"
        )

        assert entry.uri == "page.html#section"

    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            InventoryEntry(
                name="",
                domain="std",
                role="doc",
                priority=1,
                uri="page.html",
                display_name="Test"
            )


class TestValidateInventoryEntries:
    """Tests for inventory validation."""

    def test_valid_entries(self):
        entries = [
            InventoryEntry("ref1", "std", "doc", 1, "page1.html", "Page 1"),
            InventoryEntry("ref2", "std", "label", 1, "page2.html#sec", "Section"),
        ]

        issues = validate_inventory_entries(entries)
        assert len(issues) == 0

    def test_duplicate_names(self):
        entries = [
            InventoryEntry("same-name", "std", "doc", 1, "page1.html", "Page 1"),
            InventoryEntry("same-name", "std", "doc", 1, "page2.html", "Page 2"),
        ]

        issues = validate_inventory_entries(entries)
        assert len(issues) == 1
        assert "Duplicate ref name 'same-name'" in issues[0]

    def test_invalid_characters_in_name(self):
        entries = [
            InventoryEntry("valid-name", "std", "doc", 1, "page1.html", "Page 1"),
            InventoryEntry("invalid name!", "std", "doc", 1, "page2.html", "Page 2"),
            InventoryEntry("another@bad", "std", "doc", 1, "page3.html", "Page 3"),
        ]

        issues = validate_inventory_entries(entries)
        assert len(issues) == 2
        assert any("invalid name!" in issue for issue in issues)
        assert any("another@bad" in issue for issue in issues)

    def test_valid_name_patterns(self):
        entries = [
            InventoryEntry("lowercase", "std", "doc", 1, "page.html", "Page"),
            InventoryEntry("UPPERCASE", "std", "doc", 1, "page.html", "Page"),
            InventoryEntry("with-hyphens", "std", "doc", 1, "page.html", "Page"),
            InventoryEntry("with_underscores", "std", "doc", 1, "page.html", "Page"),
            InventoryEntry("with123numbers", "std", "doc", 1, "page.html", "Page"),
        ]

        issues = validate_inventory_entries(entries)
        # All names are valid
        assert len(issues) == 0

    def test_empty_entries_list(self):
        issues = validate_inventory_entries([])
        assert len(issues) == 0


class TestCreateInventory:
    """Tests for inventory creation."""

    def test_create_inventory_basic(self):
        """Test basic inventory creation."""
        entries = [
            InventoryEntry("page-ref", "std", "doc", 1, "page.html", "My Page"),
            InventoryEntry("section-ref", "std", "label", 1, "page.html#sec", "Section"),
        ]

        inv = create_inventory(entries, "Test Project", "1.0")

        assert inv.project == "Test Project"
        assert inv.version == "1.0"
        assert len(inv.objects) == 2

    def test_create_inventory_empty(self):
        """Test creating inventory with no entries."""
        inv = create_inventory([], "Test Project", "1.0")

        assert inv.project == "Test Project"
        assert inv.version == "1.0"
        assert len(inv.objects) == 0

    def test_create_inventory_default_version(self):
        """Test inventory with default version."""
        entries = [
            InventoryEntry("test", "std", "doc", 1, "page.html", "Test"),
        ]

        inv = create_inventory(entries, "Test Project")

        assert inv.version == "latest"
