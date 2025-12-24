"""Config parser for format.md files."""

import re
from pathlib import Path
from typing import Any

import yaml

from basic_memory_hooks.config import (
    CustomHookConfig,
    FormatConfig,
    HookConfig,
    HooksConfig,
    HooksStageConfig,
    NoteTypesConfig,
    ObservationCategoriesConfig,
    PostWriteHooksConfig,
    QualityConfig,
    RelationTypesConfig,
    TagTaxonomyConfig,
)

# Fields added by Basic Memory that we should ignore
BASIC_MEMORY_FIELDS = {"title", "type", "permalink", "tags"}


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract and parse YAML frontmatter from markdown content.

    Args:
        content: Raw markdown file content.

    Returns:
        Parsed frontmatter as dict, with Basic Memory fields removed.
    """
    # Match frontmatter between --- markers
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter_yaml = match.group(1)
    try:
        data = yaml.safe_load(frontmatter_yaml)
        if not isinstance(data, dict):
            return {}
    except yaml.YAMLError:
        return {}

    # Remove Basic Memory fields
    for field in BASIC_MEMORY_FIELDS:
        data.pop(field, None)

    return data


def parse_hook_config(data: dict[str, Any] | None) -> HookConfig:
    """Parse individual hook configuration."""
    if data is None:
        return HookConfig()
    return HookConfig(
        enabled=data.get("enabled", True),
        priority=data.get("priority", "normal"),
    )


def parse_hooks_stage_config(data: dict[str, Any] | None) -> HooksStageConfig:
    """Parse pre_write hooks configuration."""
    if data is None:
        return HooksStageConfig()
    return HooksStageConfig(
        validate_frontmatter=parse_hook_config(data.get("validate_frontmatter")),
        remove_duplicate_headings=parse_hook_config(data.get("remove_duplicate_headings")),
        consolidate_observations=parse_hook_config(data.get("consolidate_observations")),
        format_observations=parse_hook_config(data.get("format_observations")),
        validate_minimum_observations=parse_hook_config(data.get("validate_minimum_observations")),
        validate_note_type=parse_hook_config(data.get("validate_note_type")),
        validate_observation_categories=parse_hook_config(
            data.get("validate_observation_categories")
        ),
        validate_tag_prefixes=parse_hook_config(data.get("validate_tag_prefixes")),
        order_relations=parse_hook_config(data.get("order_relations")),
    )


def parse_post_write_hooks_config(data: dict[str, Any] | None) -> PostWriteHooksConfig:
    """Parse post_write hooks configuration."""
    if data is None:
        return PostWriteHooksConfig()
    return PostWriteHooksConfig(
        verify_relation_targets=parse_hook_config(data.get("verify_relation_targets")),
    )


def parse_config(data: dict[str, Any]) -> FormatConfig:
    """Parse configuration dict into FormatConfig.

    Args:
        data: Parsed frontmatter dict with Basic Memory fields removed.

    Returns:
        FormatConfig with values from data, defaults for missing fields.
    """
    # Memo types (note_types for backwards compatibility)
    note_types_data = data.get("note_types", data.get("memo_types", {}))
    note_types = NoteTypesConfig(
        default=note_types_data.get("default", "memo"),
        allowed=note_types_data.get(
            "allowed", ["memo", "spec", "decision", "meeting", "person", "project", "research"]
        ),
    )

    # Observation categories
    obs_data = data.get("observation_categories", {})
    observation_categories = ObservationCategoriesConfig(
        required=obs_data.get("required", ["fact", "decision", "technique"]),
        optional=obs_data.get(
            "optional", ["insight", "question", "idea", "requirement", "problem", "solution"]
        ),
    )

    # Tag taxonomy
    tag_data = data.get("tag_taxonomy", {})
    tag_taxonomy = TagTaxonomyConfig(
        enforce=tag_data.get("enforce", False),
        prefixes=tag_data.get("prefixes", {}),
    )

    # Relation types
    rel_data = data.get("relation_types", {})
    relation_types = RelationTypesConfig(
        primary=rel_data.get("primary", ["implements", "requires", "part_of"]),
        secondary=rel_data.get(
            "secondary", ["relates_to", "extends", "contrasts_with", "supersedes"]
        ),
    )

    # Quality
    quality_data = data.get("quality", {})
    quality = QualityConfig(
        minimum_observations=quality_data.get("minimum_observations", 3),
        minimum_relations=quality_data.get("minimum_relations", 1),
        require_tags=quality_data.get("require_tags", True),
        require_frontmatter=quality_data.get("require_frontmatter", ["title", "type"]),
        allow_forward_references=quality_data.get("allow_forward_references", True),
        auto_fix=quality_data.get("auto_fix", True),
    )

    # Hooks
    hooks_data = data.get("hooks", {})
    hooks = HooksConfig(
        pre_write=parse_hooks_stage_config(hooks_data.get("pre_write")),
        post_write=parse_post_write_hooks_config(hooks_data.get("post_write")),
    )

    # Custom hooks
    custom_hooks_data = data.get("custom_hooks", [])
    custom_hooks = [
        CustomHookConfig(path=h.get("path", ""), enabled=h.get("enabled", True))
        for h in custom_hooks_data
    ]

    return FormatConfig(
        version=data.get("version", "1.0"),
        strictness=data.get("strictness", "balanced"),
        note_types=note_types,
        observation_categories=observation_categories,
        tag_taxonomy=tag_taxonomy,
        relation_types=relation_types,
        quality=quality,
        hooks=hooks,
        custom_hooks=custom_hooks,
    )


def load_config_from_string(content: str) -> FormatConfig:
    """Load configuration from raw file content.

    Args:
        content: Raw format.md file content.

    Returns:
        Parsed FormatConfig.
    """
    data = parse_frontmatter(content)
    return parse_config(data)


def load_config_from_file(path: str | Path) -> FormatConfig:
    """Load configuration from file path.

    Args:
        path: Path to format.md file.

    Returns:
        Parsed FormatConfig. Returns default config if file doesn't exist.
    """
    path = Path(path)
    if not path.exists():
        return FormatConfig()

    content = path.read_text()
    return load_config_from_string(content)
