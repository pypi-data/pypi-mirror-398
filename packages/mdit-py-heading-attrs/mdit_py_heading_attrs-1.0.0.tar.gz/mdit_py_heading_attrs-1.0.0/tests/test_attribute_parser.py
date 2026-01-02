from mdit_py_heading_attrs.attribute_parser import (
    find_last_unescaped_brace,
    is_valid_id,
    parse_id_attribute,
)


class TestFindLastUnescapedBrace:
    def test_simple_brace(self):
        assert find_last_unescaped_brace("Hello {#id}") == 6

    def test_escaped_brace(self):
        assert find_last_unescaped_brace("Hello \\{not}") == -1

    def test_multiple_braces(self):
        assert find_last_unescaped_brace("Text \\{escaped} {#id}") == 16

    def test_no_brace(self):
        assert find_last_unescaped_brace("Hello world") == -1

    def test_multiple_backslashes(self):
        # Two backslashes = escaped backslash + unescaped brace
        assert find_last_unescaped_brace("Text \\\\{#id}") == 7
        # Three backslashes = escaped backslash + escaped brace
        assert find_last_unescaped_brace("Text \\\\\\{#id}") == -1

    def test_brace_at_start(self):
        assert find_last_unescaped_brace("{#id}") == 0


class TestIsValidId:
    def test_alphanumeric(self):
        assert is_valid_id("myid123") is True

    def test_with_hyphen(self):
        assert is_valid_id("my-id") is True

    def test_with_underscore(self):
        assert is_valid_id("my_id") is True

    def test_with_colon(self):
        assert is_valid_id("my:id") is True

    def test_with_period(self):
        assert is_valid_id("my.id") is True

    def test_all_special_chars(self):
        assert is_valid_id("my-id_1:2.0") is True

    def test_invalid_space(self):
        assert is_valid_id("my id") is False

    def test_invalid_special_chars(self):
        assert is_valid_id("my@id") is False
        assert is_valid_id("my#id") is False
        assert is_valid_id("my!id") is False

    def test_empty(self):
        assert is_valid_id("") is False


class TestParseIdAttribute:
    def test_basic_id(self):
        id_val, text, success = parse_id_attribute("Hello {#my-id}")
        assert success is True
        assert id_val == "my-id"
        assert text == "Hello"

    def test_id_with_special_chars(self):
        id_val, text, success = parse_id_attribute("Title {#my-id_1:2.0}")
        assert success is True
        assert id_val == "my-id_1:2.0"
        assert text == "Title"

    def test_whitespace_in_braces(self):
        id_val, text, success = parse_id_attribute("Title {  #my-id  }")
        assert success is True
        assert id_val == "my-id"

    def test_whitespace_after_braces(self):
        id_val, text, success = parse_id_attribute("Title {#my-id}  \n")
        assert success is True
        assert id_val == "my-id"

    def test_text_after_closing_brace_fails(self):
        id_val, text, success = parse_id_attribute("Title {#my-id} extra")
        assert success is False
        assert text == "Title {#my-id} extra"

    def test_escaped_brace(self):
        id_val, text, success = parse_id_attribute("Code \\{#not-id}")
        assert success is False
        assert text == "Code \\{#not-id}"

    def test_no_opening_brace(self):
        id_val, text, success = parse_id_attribute("Just text")
        assert success is False
        assert text == "Just text"

    def test_no_closing_brace(self):
        id_val, text, success = parse_id_attribute("Title {#my-id")
        assert success is False

    def test_empty_braces(self):
        id_val, text, success = parse_id_attribute("Title {}")
        assert success is False

    def test_no_hash(self):
        id_val, text, success = parse_id_attribute("Title {id}")
        assert success is False

    def test_rejects_class(self):
        id_val, text, success = parse_id_attribute("Title {.my-class}")
        assert success is False

    def test_rejects_key_value(self):
        id_val, text, success = parse_id_attribute("Title {attr=value}")
        assert success is False

    def test_rejects_multiple_attributes(self):
        """v0.1 only supports single {#id}, not multiple attributes."""
        id_val, text, success = parse_id_attribute("Title {#id .class}")
        assert success is False

    def test_invalid_id_characters(self):
        id_val, text, success = parse_id_attribute("Title {#my id}")
        assert success is False

        id_val, text, success = parse_id_attribute("Title {#my@id}")
        assert success is False

    def test_hash_only(self):
        id_val, text, success = parse_id_attribute("Title {#}")
        assert success is False

    def test_multiple_braces(self):
        id_val, text, success = parse_id_attribute("Text \\{escaped} real {#my-id}")
        assert success is True
        assert id_val == "my-id"
        assert text == "Text \\{escaped} real"

    def test_preserves_text_on_failure(self):
        original = "Title {invalid}"
        id_val, text, success = parse_id_attribute(original)
        assert success is False
        assert text == original
