# MkDocs Intersphinx Generator Plugin

A MkDocs plugin that generates Sphinx-compatible `objects.inv` files for intersphinx cross-referencing.

## Features

- **Page-level references** via YAML frontmatter
- **Header-level references** via HTML comments
- Generates Sphinx-compatible `objects.inv` files

## Installation

### Development Installation

From the plugin directory:

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### 1. Configure the Plugin

Add to your `mkdocs.yml`:

```yaml
plugins:
  - search
  - intersphinx:
      enabled: true
      project: "My Project"
      version: "latest"
```

### 2. Add References to Your Pages

#### Page-Level References (YAML Frontmatter)

```markdown
---
ref: my-page-reference
title: My Page Title
---

# My Page

Content here...
```

#### Header-Level References (HTML Comments)

```markdown
# My Page

<!-- ref:important-section -->
## Important Section

This section can be referenced by other projects.

<!-- ref:another-topic -->
### Another Topic

More content...
```

### 3. Build Your Site

```bash
mkdocs build
```

The plugin will generate `site/objects.inv` containing all references.

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the plugin |
| `project` | str | site_name | Project name for the inventory |
| `version` | str | `"latest"` | Project version |
| `output` | str | `"objects.inv"` | Output filename |
| `domain` | str | `"std"` | Sphinx domain for entries |
| `page_role` | str | `"doc"` | Role for page references |
| `header_role` | str | `"label"` | Role for header references |
| `verbose` | bool | `false` | Enable verbose logging |

## Using Generated Inventory

### From Sphinx Projects

In your Sphinx `conf.py`:

```python
intersphinx_mapping = {
    'myproject': ('https://example.com/docs/', None),
}
```

Reference in reStructuredText:

```rst
See :doc:`myproject:my-page-reference`
See :ref:`myproject:important-section`
```

### From MkDocs with mkdocstrings

In your `mkdocs.yml`:

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          import:
            - https://example.com/docs/objects.inv
```

## Development

### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov=mkdocs_intersphinx --cov-report=html
```

## How It Works

1. **Parse Phase** (`on_page_markdown`): Extract HTML ref comments and parse headers
2. **Collection Phase** (`on_page_content`): Collect inventory entries with actual anchor IDs from TOC
3. **Generation Phase** (`on_post_build`): Create and write `objects.inv` file using `sphobjinv`

## Reference Naming Guidelines

- Use lowercase letters, numbers, hyphens, and underscores only
- Use hyphens to separate words (e.g., `thread-safety-levels`)
- Make names descriptive but concise
- Ensure names are unique across your documentation

## Examples

See the `tests/` directory for example usage.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
