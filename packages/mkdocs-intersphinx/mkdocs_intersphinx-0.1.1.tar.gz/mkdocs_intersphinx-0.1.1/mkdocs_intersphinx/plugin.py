"""MkDocs plugin for generating Sphinx-compatible objects.inv files."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig

from .parser import (
    parse_page_for_refs,
    generate_anchor_id,
    RefComment
)
from .inventory import (
    InventoryEntry,
    create_inventory,
    write_inventory,
    validate_inventory_entries
)

logger = logging.getLogger('mkdocs.plugins.intersphinx')


class IntersphinxPlugin(BasePlugin):
    """
    MkDocs plugin to generate Sphinx-compatible objects.inv for intersphinx.

    This plugin extracts references from:
    1. YAML frontmatter (ref: page-name)
    2. HTML comments (<!-- ref:header-name -->)

    And generates an objects.inv file that can be used by Sphinx intersphinx
    or mkdocstrings to cross-reference this documentation.
    """

    config_scheme = (
        ('enabled', config_options.Type(bool, default=True)),
        ('project', config_options.Type(str, default=None)),
        ('version', config_options.Type(str, default='latest')),
        ('output', config_options.Type(str, default='objects.inv')),
        ('domain', config_options.Type(str, default='std')),
        ('page_role', config_options.Type(str, default='doc')),
        ('header_role', config_options.Type(str, default='label')),
        ('auto_ref_pages', config_options.Type(bool, default=False)),
        ('verbose', config_options.Type(bool, default=False)),
    )

    def __init__(self) -> None:
        super().__init__()
        self.inventory_entries: List[InventoryEntry] = []
        self._logger = logging.getLogger('mkdocs.plugins.intersphinx')

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """
        Initialize plugin with MkDocs config.

        Args:
            config: MkDocs configuration object

        Returns:
            Modified config object
        """
        if not self.config['project']:
            self.config['project'] = config.get('site_name', 'Documentation')

        if self.config['verbose']:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

        self._logger.info(
            f"Intersphinx generator initialized for project: {self.config['project']}"
        )

        return config

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files
    ) -> str:
        """
        Extract HTML ref comments from markdown before processing.

        This hook runs before markdown is converted to HTML, allowing us to
        parse the raw markdown content for HTML ref comments.

        Args:
            markdown: Raw markdown content
            page: Page object
            config: MkDocs config
            files: All files in the site

        Returns:
            Unmodified markdown content
        """
        if not self.config['enabled']:
            return markdown

        ref_comments, headers = parse_page_for_refs(markdown)

        if not hasattr(page, 'meta'):
            page.meta = {}

        page.meta['_intersphinx_refs'] = ref_comments
        page.meta['_intersphinx_headers'] = headers

        if ref_comments:
            self._logger.debug(
                f"Found {len(ref_comments)} ref comments in {page.file.src_path}"
            )

        return markdown

    def on_page_content(
        self,
        html: str,
        page: Page,
        config: MkDocsConfig,
        files: Files
    ) -> str:
        """
        Collect inventory entries after HTML generation.

        This hook runs after markdown is converted to HTML and the TOC is
        generated, allowing us to access the actual anchors for headers.

        Args:
            html: Generated HTML content
            page: Page object with TOC
            config: MkDocs config
            files: All files in the site

        Returns:
            Unmodified HTML content
        """
        if not self.config['enabled']:
            return html

        if 'ref' in page.meta:
            self._add_page_entry(page)

        if '_intersphinx_refs' in page.meta:
            self._add_header_entries(page)

        return html

    def on_post_build(self, config: MkDocsConfig) -> None:
        """
        Generate and write objects.inv file after site is built.

        This hook runs after all pages are processed and the site is built.
        We generate the final inventory file here.

        Args:
            config: MkDocs configuration
        """
        if not self.config['enabled']:
            return

        # Add automatic index entry if not already present
        self._add_index_entry()

        if not self.inventory_entries:
            self._logger.warning("No inventory entries collected. objects.inv will be empty.")
            return

        issues = validate_inventory_entries(self.inventory_entries)
        if issues:
            self._logger.warning(
                f"Found {len(issues)} validation issues in inventory entries:"
            )
            for issue in issues:
                self._logger.warning(f"  - {issue}")

        try:
            inv = create_inventory(
                self.inventory_entries,
                self.config['project'],
                self.config['version']
            )

            # Write to site directory
            output_path = Path(config['site_dir']) / self.config['output']
            write_inventory(inv, output_path)

            self._logger.info(
                f"Generated {output_path} with {len(self.inventory_entries)} entries"
            )

            if self.config['verbose']:
                self._logger.debug("Inventory entries:")
                for entry in self.inventory_entries:
                    self._logger.debug(
                        f"  {entry.name} -> {entry.uri} ({entry.role})"
                    )

        except Exception as e:
            self._logger.error(f"Failed to generate inventory: {e}", exc_info=True)
            raise

    def _add_page_entry(self, page: Page) -> None:
        """
        Add page-level inventory entry from YAML frontmatter ref.

        Args:
            page: Page object with 'ref' in meta
        """
        ref_name = page.meta['ref']

        # Page URL should already be relative (e.g., 'porting.html')
        # If it ends with 'index.html', we might want to strip that
        uri = page.url

        entry = InventoryEntry(
            name=ref_name,
            domain=self.config['domain'],
            role=self.config['page_role'],
            priority=1,
            uri=uri,
            display_name=page.title or ref_name
        )

        self.inventory_entries.append(entry)

        self._logger.debug(
            f"Added page entry: {ref_name} -> {uri}"
        )

    def _add_header_entries(self, page: Page) -> None:
        """
        Add header-level inventory entries from HTML ref comments.

        Args:
            page: Page object with '_intersphinx_refs' in meta
        """
        ref_comments: List[RefComment] = page.meta.get('_intersphinx_refs', [])

        for ref in ref_comments:
            if not ref.next_header_text:
                self._logger.warning(
                    f"Ref comment '{ref.name}' in {page.file.src_path} "
                    f"at line {ref.line_number} has no following header. Skipping."
                )
                continue

            anchor = self._find_anchor_from_toc(page, ref.next_header_text)

            if not anchor:
                anchor = generate_anchor_id(ref.next_header_text)
                self._logger.debug(
                    f"Could not find anchor in TOC for '{ref.next_header_text}', "
                    f"using generated anchor: {anchor}"
                )

            uri = f"{page.url}#{anchor}"

            entry = InventoryEntry(
                name=ref.name,
                domain=self.config['domain'],
                role=self.config['header_role'],
                priority=1,
                uri=uri,
                display_name=ref.next_header_text
            )

            self.inventory_entries.append(entry)

            self._logger.debug(
                f"Added header entry: {ref.name} -> {uri}"
            )

    def _add_index_entry(self) -> None:
        """
        Add automatic inventory entry for the index/root page.

        Creates an entry named "index" pointing to the root of the website
        if one doesn't already exist.
        """
        # Check if an index entry already exists
        if any(entry.name == 'index' for entry in self.inventory_entries):
            self._logger.debug("Index entry already exists, skipping automatic creation")
            return

        # Create automatic index entry, using / for root URL
        entry = InventoryEntry(
            name='index',
            domain=self.config['domain'],
            role=self.config['page_role'],
            priority=1,
            uri='',
            display_name='Index'
        )

        self.inventory_entries.append(entry)

        self._logger.debug("Added automatic index entry: index -> /")

    def _find_anchor_from_toc(self, page: Page, header_text: str) -> Optional[str]:
        """
        Find the anchor ID from page TOC by matching header text.

        Args:
            page: Page object with toc attribute
            header_text: Header text to search for

        Returns:
            Anchor ID if found, None otherwise
        """
        if not hasattr(page, 'toc') or not page.toc:
            return None

        def search_toc_items(items: Any) -> Optional[str]:
            for item in items:
                if hasattr(item, 'title') and item.title == header_text:
                    return item.id if hasattr(item, 'id') else None

                if hasattr(item, 'children') and item.children:
                    result = search_toc_items(item.children)
                    if result:
                        return result

            return None

        return search_toc_items(page.toc.items) if hasattr(page.toc, 'items') else None
