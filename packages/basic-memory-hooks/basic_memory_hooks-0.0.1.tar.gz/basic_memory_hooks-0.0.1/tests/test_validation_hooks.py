"""Tests for validation hooks."""

import pytest

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.hooks.validation import (
    ValidateFrontmatterHook,
    ValidateMinimumObservationsHook,
    ValidateNoteTypeHook,
    ValidateObservationCategoriesHook,
    ValidateTagPrefixesHook,
    VerifyRelationTargetsHook,
)
from basic_memory_hooks.types import HookContext, HookStage


@pytest.fixture
def config():
    return FormatConfig()


class TestValidateFrontmatterHook:
    def test_valid_frontmatter(self, config):
        hook = ValidateFrontmatterHook(config)
        content = """---
title: Test Note
type: memo
---

# Test Note
"""
        ctx = HookContext(content=content, title="Test Note")
        result = hook.execute(ctx)
        assert result.success is True
        assert len(result.errors) == 0

    def test_missing_frontmatter(self, config):
        hook = ValidateFrontmatterHook(config)
        content = "# Test Note\n\nNo frontmatter here."
        ctx = HookContext(content=content, title="Test Note")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Missing YAML frontmatter" in result.errors[0]

    def test_missing_required_field(self, config):
        hook = ValidateFrontmatterHook(config)
        content = """---
title: Test Note
---

# Missing type field
"""
        ctx = HookContext(content=content, title="Test Note")
        result = hook.execute(ctx)
        assert result.success is False
        assert any("type" in e for e in result.errors)

    def test_stage_and_priority(self, config):
        hook = ValidateFrontmatterHook(config)
        assert hook.stage == HookStage.PRE_WRITE
        assert hook.name == "validate_frontmatter"


class TestValidateMinimumObservationsHook:
    def test_sufficient_observations(self, config):
        hook = ValidateMinimumObservationsHook(config)
        content = """---
title: Test
type: memo
---

## Observations
- [fact] First observation
- [decision] Second observation
- [technique] Third observation
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True

    def test_insufficient_observations(self, config):
        hook = ValidateMinimumObservationsHook(config)
        content = """---
title: Test
type: memo
---

## Observations
- [fact] Only one observation
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Insufficient observations" in result.errors[0]

    def test_missing_observations_section(self, config):
        hook = ValidateMinimumObservationsHook(config)
        content = """---
title: Test
type: memo
---

# Test Note

No observations section.
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Missing ## Observations section" in result.errors[0]


class TestValidateNoteTypeHook:
    def test_valid_type(self, config):
        hook = ValidateNoteTypeHook(config)
        content = """---
title: Test
type: memo
---
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True

    def test_invalid_type(self, config):
        hook = ValidateNoteTypeHook(config)
        content = """---
title: Test
type: invalid_type
---
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Invalid note type" in result.errors[0]

    def test_no_type_specified(self, config):
        hook = ValidateNoteTypeHook(config)
        content = """---
title: Test
---
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        # No type is acceptable (will use default)
        assert result.success is True


class TestValidateObservationCategoriesHook:
    def test_all_required_categories(self, config):
        hook = ValidateObservationCategoriesHook(config)
        content = """---
title: Test
type: memo
---

## Observations
- [fact] A fact
- [decision] A decision
- [technique] A technique
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True

    def test_missing_required_category(self, config):
        hook = ValidateObservationCategoriesHook(config)
        content = """---
title: Test
type: memo
---

## Observations
- [fact] Only facts here
- [decision] And decisions
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Missing required observation categories" in result.errors[0]

    def test_invalid_category(self, config):
        hook = ValidateObservationCategoriesHook(config)
        content = """---
title: Test
type: memo
---

## Observations
- [fact] A fact
- [decision] A decision
- [technique] A technique
- [invalid_cat] Invalid category
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "Invalid observation categories" in result.errors[0]


class TestValidateTagPrefixesHook:
    def test_should_run_when_enforce_disabled(self, config):
        config.tag_taxonomy.enforce = False
        hook = ValidateTagPrefixesHook(config)
        ctx = HookContext(content="test", title="Test")
        assert hook.should_run(ctx) is False

    def test_should_run_when_enforce_enabled(self, config):
        config.tag_taxonomy.enforce = True
        hook = ValidateTagPrefixesHook(config)
        ctx = HookContext(content="test", title="Test")
        assert hook.should_run(ctx) is True

    def test_valid_prefixed_tags(self, config):
        config.tag_taxonomy.enforce = True
        config.tag_taxonomy.prefixes = {"project": "Projects", "topic": "Topics"}
        hook = ValidateTagPrefixesHook(config)
        content = """---
title: Test
type: memo
tags:
- project/my-project
- topic/python
---
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True

    def test_invalid_unprefixed_tags(self, config):
        config.tag_taxonomy.enforce = True
        config.tag_taxonomy.prefixes = {"project": "Projects"}
        hook = ValidateTagPrefixesHook(config)
        content = """---
title: Test
type: memo
tags:
- python
- project/valid
---
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is False
        assert "python" in result.errors[0]


class TestVerifyRelationTargetsHook:
    def test_stage_is_post_write(self, config):
        hook = VerifyRelationTargetsHook(config)
        assert hook.stage == HookStage.POST_WRITE

    def test_extracts_relation_targets(self, config):
        hook = VerifyRelationTargetsHook(config)
        content = """---
title: Test
type: memo
---

## Relations
- implements [[Feature A]]
- requires [[Component B]]
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert "relation_targets" in result.metadata
        assert "Feature A" in result.metadata["relation_targets"]
        assert "Component B" in result.metadata["relation_targets"]

    def test_no_relations(self, config):
        hook = VerifyRelationTargetsHook(config)
        content = """---
title: Test
type: memo
---

No relations section.
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
