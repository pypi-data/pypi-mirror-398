"""Tests for the learn module."""

import json


def strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from text (duplicating logic for testing)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


class TestMarkdownFenceStripping:
    """Tests for markdown fence stripping logic."""

    def test_plain_json(self):
        """Plain JSON should pass through unchanged."""
        text = '{"key": "value"}'
        result = strip_markdown_fences(text)
        assert json.loads(result) == {"key": "value"}

    def test_json_with_fences(self):
        """JSON with markdown fences should be stripped."""
        text = '```json\n{"key": "value"}\n```'
        result = strip_markdown_fences(text)
        assert json.loads(result) == {"key": "value"}

    def test_json_with_plain_fences(self):
        """JSON with plain fences (no language) should be stripped."""
        text = '```\n{"key": "value"}\n```'
        result = strip_markdown_fences(text)
        assert json.loads(result) == {"key": "value"}

    def test_json_with_uppercase_fences(self):
        """JSON with uppercase JSON tag should be stripped."""
        text = '```JSON\n{"key": "value"}\n```'
        result = strip_markdown_fences(text)
        assert json.loads(result) == {"key": "value"}

    def test_multiline_json(self):
        """Multiline JSON with fences should be stripped."""
        text = """```json
{
    "schema": {
        "id": "string",
        "name": "string"
    },
    "rules": ["rule1", "rule2"]
}
```"""
        result = strip_markdown_fences(text)
        parsed = json.loads(result)
        assert "schema" in parsed
        assert "rules" in parsed

    def test_whitespace_handling(self):
        """Extra whitespace should be handled."""
        text = '  ```json\n{"key": "value"}\n```  '
        result = strip_markdown_fences(text)
        assert json.loads(result) == {"key": "value"}
