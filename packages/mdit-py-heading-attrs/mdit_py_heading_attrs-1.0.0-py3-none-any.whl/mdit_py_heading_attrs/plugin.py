from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore

from .attribute_parser import parse_id_attribute


def heading_attrs_plugin(md: MarkdownIt) -> None:
    """Add ID attribute support to headings.

    Supports following attribute syntax:
    - ## Heading {#id}
    - ## Heading ## {#id}
    - Heading {#id}
      ========

    Args:
        md: MarkdownIt instance

    Example:
        >>> from markdown_it import MarkdownIt
        >>> from mdit_py_heading_attrs import heading_attrs_plugin
        >>> md = MarkdownIt().use(heading_attrs_plugin)
        >>> html = md.render("## Hello {#my-id}")
        >>> assert 'id="my-id"' in html
    """

    def heading_attrs_core_rule(state: StateCore) -> None:
        """Core rule to parse and apply heading ID attributes.

        Processes token stream after inline parsing to:
        1. Find heading_open tokens
        2. Check if inline content ends with {#id}
        3. Extract and validate the ID
        4. Apply ID to heading_open token
        5. Remove {#id} from text content
        """
        tokens = state.tokens
        i = 0

        while i < len(tokens):
            # Look for heading_open tokens
            if tokens[i].type != "heading_open":
                i += 1
                continue

            # Must have the triple: heading_open, inline, heading_close
            if i + 2 >= len(tokens):
                i += 1
                continue

            if tokens[i + 1].type != "inline":
                i += 1
                continue

            heading_open = tokens[i]
            inline_token = tokens[i + 1]

            # Skip if no children
            if not inline_token.children:
                i += 1
                continue

            # Get the last text token (attributes should be at the end)
            last_child = inline_token.children[-1]

            if last_child.type != "text":
                i += 1
                continue

            # Try to parse ID attribute from the text content
            text_content = last_child.content
            id_value, new_text, success = parse_id_attribute(text_content)

            if not success or not id_value:
                i += 1
                continue

            # Apply ID to heading_open token
            heading_open.attrSet("id", id_value)

            # Update the text content to remove the attribute block
            if new_text:
                last_child.content = new_text
            else:
                # Remove the last text token if it's now empty
                inline_token.children = inline_token.children[:-1]

            i += 1

    # Register core rule after inline parsing
    md.core.ruler.after("inline", "heading_attrs", heading_attrs_core_rule)
