from markdown_it import MarkdownIt

from mdit_py_heading_attrs import heading_attrs_plugin


class TestBasicIdParsing:
    def test_basic_atx_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#my-id}")
        assert html == '<h2 id="my-id">Title</h2>\n'

    def test_h1_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("# Heading {#h1-id}")
        assert html == '<h1 id="h1-id">Heading</h1>\n'

    def test_h3_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("### Heading {#h3-id}")
        assert html == '<h3 id="h3-id">Heading</h3>\n'

    def test_h4_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("#### Heading {#h4-id}")
        assert html == '<h4 id="h4-id">Heading</h4>\n'

    def test_h5_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("##### Heading {#h5-id}")
        assert html == '<h5 id="h5-id">Heading</h5>\n'

    def test_h6_heading(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("###### Heading {#h6-id}")
        assert html == '<h6 id="h6-id">Heading</h6>\n'


class TestAtxWithClosingHashes:
    def test_atx_with_closing_hashes(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title ## {#my-id}")
        assert html == '<h2 id="my-id">Title ##</h2>\n'

    def test_h1_with_closing(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("# Heading # {#h1-id}")
        assert html == '<h1 id="h1-id">Heading #</h1>\n'


class TestSetextHeadings:
    def test_setext_h1(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("Title {#my-id}\n=====")
        assert html == '<h1 id="my-id">Title</h1>\n'

    def test_setext_h2(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("Subtitle {#sub-id}\n-------")
        assert html == '<h2 id="sub-id">Subtitle</h2>\n'


class TestSpecialIdCharacters:
    def test_id_with_hyphen(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#my-special-id}")
        assert html == '<h2 id="my-special-id">Title</h2>\n'

    def test_id_with_underscore(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#my_special_id}")
        assert html == '<h2 id="my_special_id">Title</h2>\n'

    def test_id_with_colon(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#section:subsection}")
        assert html == '<h2 id="section:subsection">Title</h2>\n'

    def test_id_with_period(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#version.1.0}")
        assert html == '<h2 id="version.1.0">Title</h2>\n'

    def test_id_with_all_special_chars(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#my-id_1:2.0}")
        assert html == '<h2 id="my-id_1:2.0">Title</h2>\n'


class TestInlineContent:
    def test_heading_with_emphasis(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## *Emphasized* Title {#my-id}")
        assert html == '<h2 id="my-id"><em>Emphasized</em> Title</h2>\n'

    def test_heading_with_strong(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## **Bold** Title {#my-id}")
        assert html == '<h2 id="my-id"><strong>Bold</strong> Title</h2>\n'

    def test_heading_with_code(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Using `code` here {#my-id}")
        assert html == '<h2 id="my-id">Using <code>code</code> here</h2>\n'

    def test_heading_with_link(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## See [link](http://example.com) {#my-id}")
        assert html == '<h2 id="my-id">See <a href="http://example.com">link</a></h2>\n'


class TestEdgeCases:
    def test_escaped_braces(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Code \\{#not-id}")
        assert html == '<h2>Code {#not-id}</h2>\n'

    def test_whitespace_in_braces(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {  #my-id  }")
        assert html == '<h2 id="my-id">Title</h2>\n'

    def test_whitespace_after_braces(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#my-id}  \n")
        assert html == '<h2 id="my-id">Title</h2>\n'

    def test_empty_braces(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {}")
        assert html == '<h2>Title {}</h2>\n'

    def test_no_hash_symbol(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {id}")
        assert html == '<h2>Title {id}</h2>\n'

    def test_heading_without_attributes(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Normal Heading")
        assert html == '<h2>Normal Heading</h2>\n'


class TestMultipleHeadings:
    def test_multiple_headings_with_ids(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        markdown = """# First {#first}
## Second {#second}
### Third {#third}"""
        html = md.render(markdown)
        expected = """<h1 id="first">First</h1>
<h2 id="second">Second</h2>
<h3 id="third">Third</h3>
"""
        assert html == expected

    def test_mixed_headings(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        markdown = """# With ID {#my-id}
## Without ID
### Another with ID {#another}"""
        html = md.render(markdown)
        expected = """<h1 id="my-id">With ID</h1>
<h2>Without ID</h2>
<h3 id="another">Another with ID</h3>
"""
        assert html == expected


class TestRejectedPatterns:
    """v0.1 rejects unsupported syntax - renders literally."""

    def test_rejects_class_syntax(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {.my-class}")
        assert html == '<h2>Title {.my-class}</h2>\n'

    def test_rejects_key_value_syntax(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {data-value=test}")
        assert html == '<h2>Title {data-value=test}</h2>\n'

    def test_rejects_multiple_attributes(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Title {#id .class}")
        assert html == '<h2>Title {#id .class}</h2>\n'

    def test_rejects_quoted_values(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render('## Title {title="My Title"}')
        assert html == '<h2>Title {title=&quot;My Title&quot;}</h2>\n'


class TestComplexExamples:
    def test_full_document(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        markdown = """# Introduction {#intro}

This is some text.

## Getting Started {#getting-started}

More text here.

### Installation {#installation}

Code example:

    npm install package

### Configuration {#config}

Some configuration details.

## Advanced Usage

This section has no ID."""

        html = md.render(markdown)
        expected = """<h1 id="intro">Introduction</h1>
<p>This is some text.</p>
<h2 id="getting-started">Getting Started</h2>
<p>More text here.</p>
<h3 id="installation">Installation</h3>
<p>Code example:</p>
<pre><code>npm install package
</code></pre>
<h3 id="config">Configuration</h3>
<p>Some configuration details.</p>
<h2>Advanced Usage</h2>
<p>This section has no ID.</p>
"""
        assert html == expected

    def test_id_with_numbers(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        html = md.render("## Version 2.0 {#v2-0}")
        assert html == '<h2 id="v2-0">Version 2.0</h2>\n'

    def test_very_long_id(self):
        md = MarkdownIt().use(heading_attrs_plugin)
        long_id = "very-long-id-" + "a" * 100
        html = md.render(f"## Title {{#{long_id}}}")
        assert html == f'<h2 id="{long_id}">Title</h2>\n'
