import json

from multimodal_agent.cli.formatting import (
    detect_content_type,
    format_code,
    format_json,
    format_output,
    format_plain,
    format_xml_html,
)


def test_detect_json():
    assert detect_content_type('{"a": 1}') == "json"
    assert detect_content_type("[1, 2, 3]") == "json"


def test_detect_code():
    assert detect_content_type("```python\nprint('x')\n```") == "code"
    assert detect_content_type("def hello():\n    pass") == "code"


def test_detect_xml_html():
    assert detect_content_type("<root></root>") == "xml"
    assert detect_content_type("<html><body></body></html>") == "html"


def test_detect_plain():
    assert detect_content_type("Hello world") == "plain"
    assert detect_content_type("") == "plain"


def test_format_json_pretty():
    raw = '{"a":1,"b":2}'
    formatted = format_json(raw)
    assert formatted.startswith("{\n  ")
    parsed = json.loads(formatted)
    assert parsed["a"] == 1


def test_format_code_backticks():
    code = "print('hello')"
    formatted = format_code(code)
    assert formatted.startswith("```")
    assert formatted.endswith("```")
    assert "print('hello')" in formatted


def test_format_xml():
    xml = "<root><x>1</x></root>"
    formatted = format_xml_html(xml)
    assert formatted.strip().startswith("<?xml")


def test_format_plain_removes_extra_blank_lines():
    raw = "hello\n\n\n\nworld"
    formatted = format_plain(raw)
    assert formatted == "hello\n\nworld"


def test_format_output_json():
    raw = '{"a":1}'
    formatted = format_output(raw)
    assert formatted.startswith("{")
    assert "  " in formatted  # pretty printed


def test_format_output_code():
    raw = "print('x')"
    formatted = format_output(raw)
    assert formatted.startswith("```")
