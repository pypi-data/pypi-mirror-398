# mdit-py-heading-attrs

[![PyPI version](https://img.shields.io/pypi/v/mdit-py-heading-attrs.svg)](https://pypi.org/project/mdit-py-heading-attrs/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdit-py-heading-attrs.svg)](https://pypi.org/project/mdit-py-heading-attrs/)
[![License](https://img.shields.io/pypi/l/mdit-py-heading-attrs.svg)](https://github.com/mangoumbrella/mdit-py-heading-attrs/blob/main/LICENSE)

[mdit-py-heading-attrs](https://github.com/mangoumbrella/mdit-py-heading-attrs) is a
[markdown-it-py](https://github.com/executablebooks/markdown-it-py) plugin to add attribute support to headings. Currently, only anchors are supported.

## Example

**Input markdown:**
```markdown
## Getting Started {#getting-started}
```

**Output HTML:**
```html
<h2 id="getting-started">Getting Started</h2>
```

## Installation

```bash
pip install mdit-py-heading-attrs
```

Or with uv:

```bash
uv add mdit-py-heading-attrs
```

## Usage

```python
from markdown_it import MarkdownIt
from mdit_py_heading_attrs import heading_attrs_plugin

md = MarkdownIt().use(heading_attrs_plugin)

markdown = """
## Getting Started {#getting-started}
"""

html = md.render(markdown)
print(html)
```

Output:
```html
<h2 id="getting-started">Getting Started</h2>
```

## Syntax

Add an ID to any heading using `{#id}` syntax at the end:

```markdown
## Heading {#my-id}
```

### Supported Heading Formats

```markdown
# ATX heading {#h1-id}
## ATX heading {#h2-id}
### ATX heading {#h3-id}

## ATX with closing ## {#my-id}

Setext H1 {#setext-h1}
==========

Setext H2 {#setext-h2}
----------
```

### Escaping

Use backslash to escape braces if you want them to render literally:

```markdown
## Code Example \{not-an-id\}
```

Renders as:
```html
<h2>Code Example {not-an-id}</h2>
```

## See Also

- [mdit-py-plugins](https://github.com/executablebooks/mdit-py-plugins): collection of core plugins for markdown-it-py.
- [mdit-py-figure](https://github.com/mangoumbrella/mdit-py-figure): plugin to parse markdown paragraphs that start with an image into HTML `<figure>` elements.

## Changelog

See [CHANGELOG.md](https://github.com/mangoumbrella/mdit-py-heading-attrs/blob/main/CHANGELOG.md).

## License

Apache-2.0
