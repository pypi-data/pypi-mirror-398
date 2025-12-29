"""Generate Sphinx-compatible objects.inv files."""

from dataclasses import dataclass
from pathlib import Path
from typing import List
import logging
import re

from sphobjinv import Inventory, DataObjStr, writebytes, compress  # type: ignore[import-untyped]

logger = logging.getLogger('mkdocs.plugins.intersphinx')


@dataclass
class InventoryEntry:
    """Represents a single entry in the intersphinx inventory."""
    name: str              # Reference name (from YAML or HTML comment)
    domain: str            # 'std' for standard domain
    role: str              # 'doc' for pages, 'label' for headers
    priority: int          # 1 for standard priority
    uri: str               # Relative URI (e.g., 'porting.html#atomic-ops')
    display_name: str      # Display text (e.g., 'Atomic Operations')

    def __post_init__(self) -> None:
        """Validate entry data."""
        if not self.name:
            raise ValueError("Entry name cannot be empty")
        if self.priority not in (-1, 1):
            logger.warning(f"Unusual priority {self.priority} for {self.name}")


def create_inventory(
    entries: List[InventoryEntry],
    project: str,
    version: str = "latest"
) -> Inventory:
    """
    Create a Sphinx inventory from collected entries.

    Args:
        entries: List of inventory entries to include
        project: Project name for the inventory
        version: Project version for the inventory

    Returns:
        Inventory object ready to be written
    """
    if not entries:
        logger.warning("Creating inventory with no entries")

    inv = Inventory()
    inv.project = project
    inv.version = version

    for entry in entries:
        # Create DataObjStr for each entry
        # DataObjStr format: name domain:role priority uri dispname
        # dispname of '-' means use name as display name
        data_obj = DataObjStr(
            name=entry.name,
            domain=entry.domain,
            role=entry.role,
            priority=str(entry.priority),
            uri=entry.uri,
            dispname=entry.display_name if entry.display_name else '-'
        )
        inv.objects.append(data_obj)

    logger.info(f"Created inventory with {len(entries)} entries")
    return inv


def write_inventory(inv: Inventory, output_path: Path) -> None:
    """
    Write inventory to objects.inv file with proper zlib compression.

    Args:
        inv: Inventory object to write
        output_path: Path where objects.inv should be written

    Raises:
        IOError: If file cannot be written
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate plaintext inventory bytes
        plaintext_bytes = inv.data_file()

        # Compress using sphobjinv.compress()
        # This compresses the data lines while keeping the header uncompressed
        compressed_bytes = compress(plaintext_bytes)

        # Write to file using sphobjinv's writebytes function
        writebytes(str(output_path), compressed_bytes)

        logger.info(f"Wrote inventory to {output_path}")
        logger.debug(
            f"Inventory size: {len(plaintext_bytes)} bytes plaintext, "
            f"{len(compressed_bytes)} bytes compressed"
        )
    except Exception as e:
        logger.error(f"Failed to write inventory to {output_path}: {e}")
        raise


def validate_inventory_entries(entries: List[InventoryEntry]) -> List[str]:
    """
    Validate inventory entries and return list of warnings/errors.

    Args:
        entries: List of inventory entries to validate

    Returns:
        List of warning/error messages (empty if all valid)
    """
    issues = []

    # Check for duplicate names
    names: dict[str, str] = {}
    for entry in entries:
        if entry.name in names:
            issues.append(
                f"Duplicate ref name '{entry.name}' found in "
                f"{entry.uri} and {names[entry.name]}"
            )
        else:
            names[entry.name] = entry.uri

    # Check for invalid characters in names
    valid_name_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    for entry in entries:
        if not valid_name_pattern.match(entry.name):
            issues.append(
                f"Invalid ref name '{entry.name}' in {entry.uri}. "
                f"Use only letters, numbers, hyphens, and underscores."
            )

    return issues
