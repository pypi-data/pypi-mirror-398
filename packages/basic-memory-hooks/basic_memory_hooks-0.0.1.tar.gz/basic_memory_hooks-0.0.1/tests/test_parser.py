"""Tests for parser module."""

import pytest

from basic_memory_hooks.parser import (
    load_config_from_string,
    parse_config,
    parse_frontmatter,
)


class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = """---
version: "1.0"
strictness: strict
---

# Content here
"""
        data = parse_frontmatter(content)
        assert data["version"] == "1.0"
        assert data["strictness"] == "strict"

    def test_no_frontmatter(self):
        content = "# Just content"
        data = parse_frontmatter(content)
        assert data == {}

    def test_invalid_frontmatter(self):
        content = """---
invalid: yaml: here
---
"""
        data = parse_frontmatter(content)
        # Should return empty dict on parse error
        assert data == {}

    def test_basic_memory_fields_removed(self):
        content = """---
title: My Note
type: memo
permalink: my-note
tags:
  - test
custom_field: value
---
"""
        data = parse_frontmatter(content)
        assert "title" not in data
        assert "type" not in data
        assert "permalink" not in data
        assert "tags" not in data
        assert data["custom_field"] == "value"


class TestParseConfig:
    def test_empty_config(self):
        config = parse_config({})
        assert config.version == "1.0"
        assert config.strictness == "balanced"
        assert config.note_types.default == "memo"

    def test_full_config(self):
        data = {
            "version": "2.0",
            "strictness": "strict",
            "note_types": {
                "default": "spec",
                "allowed": ["spec", "note"],
            },
            "observation_categories": {
                "required": ["fact"],
                "optional": ["idea"],
            },
            "quality": {
                "minimum_observations": 5,
            },
        }
        config = parse_config(data)
        assert config.version == "2.0"
        assert config.strictness == "strict"
        assert config.note_types.default == "spec"
        assert config.note_types.allowed == ["spec", "note"]
        assert config.observation_categories.required == ["fact"]
        assert config.quality.minimum_observations == 5


class TestLoadConfigFromString:
    def test_load_complete_config(self):
        content = """---
title: Format Config
type: config
version: "1.0"
strictness: strict
note_types:
  default: memo
  allowed:
    - memo
    - spec
quality:
  minimum_observations: 3
---

# Format Configuration

This is the format configuration file.
"""
        config = load_config_from_string(content)
        assert config.strictness == "strict"
        assert config.note_types.allowed == ["memo", "spec"]
        assert config.quality.minimum_observations == 3

    def test_load_minimal_config(self):
        content = """---
title: Format
type: config
---

# Minimal config
"""
        config = load_config_from_string(content)
        # Should use defaults
        assert config.version == "1.0"
        assert config.strictness == "balanced"


class TestStrictnessMethods:
    def test_is_strict(self):
        config = parse_config({"strictness": "strict"})
        assert config.is_strict() is True
        assert config.is_balanced() is False
        assert config.is_flexible() is False

    def test_is_balanced(self):
        config = parse_config({"strictness": "balanced"})
        assert config.is_strict() is False
        assert config.is_balanced() is True
        assert config.is_flexible() is False

    def test_is_flexible(self):
        config = parse_config({"strictness": "flexible"})
        assert config.is_strict() is False
        assert config.is_balanced() is False
        assert config.is_flexible() is True
