"""Configuration schema for Basic Memory Hooks."""

from dataclasses import dataclass, field


@dataclass
class MemoTypesConfig:
    """Memo types configuration."""

    default: str = "memo"
    allowed: list[str] = field(
        default_factory=lambda: [
            "memo",
            "spec",
            "decision",
            "meeting",
            "person",
            "project",
            "research",
        ]
    )


# Alias for backwards compatibility
NoteTypesConfig = MemoTypesConfig


@dataclass
class ObservationCategoriesConfig:
    """Observation categories configuration."""

    required: list[str] = field(default_factory=lambda: ["fact", "decision", "technique"])
    optional: list[str] = field(
        default_factory=lambda: [
            "insight",
            "question",
            "idea",
            "requirement",
            "problem",
            "solution",
        ]
    )


@dataclass
class TagTaxonomyConfig:
    """Tag taxonomy configuration."""

    enforce: bool = False
    prefixes: dict[str, str] = field(default_factory=dict)


@dataclass
class RelationTypesConfig:
    """Relation types configuration."""

    primary: list[str] = field(default_factory=lambda: ["implements", "requires", "part_of"])
    secondary: list[str] = field(
        default_factory=lambda: ["relates_to", "extends", "contrasts_with", "supersedes"]
    )


@dataclass
class QualityConfig:
    """Quality rules configuration."""

    minimum_observations: int = 3
    minimum_relations: int = 1
    require_tags: bool = True
    require_frontmatter: list[str] = field(default_factory=lambda: ["title", "type"])
    allow_forward_references: bool = True
    auto_fix: bool = True


@dataclass
class HookConfig:
    """Individual hook configuration."""

    enabled: bool = True
    priority: str = "normal"  # first, high, normal, low, last


@dataclass
class HooksStageConfig:
    """Hooks configuration for a stage."""

    validate_frontmatter: HookConfig = field(default_factory=lambda: HookConfig(priority="first"))
    remove_duplicate_headings: HookConfig = field(
        default_factory=lambda: HookConfig(priority="high")
    )
    consolidate_observations: HookConfig = field(
        default_factory=lambda: HookConfig(priority="high")
    )
    format_observations: HookConfig = field(default_factory=HookConfig)
    validate_minimum_observations: HookConfig = field(default_factory=HookConfig)
    validate_note_type: HookConfig = field(default_factory=HookConfig)
    validate_observation_categories: HookConfig = field(default_factory=HookConfig)
    validate_tag_prefixes: HookConfig = field(default_factory=HookConfig)
    order_relations: HookConfig = field(default_factory=HookConfig)


@dataclass
class PostWriteHooksConfig:
    """Post-write hooks configuration."""

    verify_relation_targets: HookConfig = field(default_factory=HookConfig)


@dataclass
class HooksConfig:
    """All hooks configuration."""

    pre_write: HooksStageConfig = field(default_factory=HooksStageConfig)
    post_write: PostWriteHooksConfig = field(default_factory=PostWriteHooksConfig)


@dataclass
class CustomHookConfig:
    """Custom hook configuration."""

    path: str = ""
    enabled: bool = True


@dataclass
class FormatConfig:
    """Complete format configuration."""

    version: str = "1.0"
    strictness: str = "balanced"  # strict, balanced, flexible
    note_types: MemoTypesConfig = field(default_factory=MemoTypesConfig)
    observation_categories: ObservationCategoriesConfig = field(
        default_factory=ObservationCategoriesConfig
    )
    tag_taxonomy: TagTaxonomyConfig = field(default_factory=TagTaxonomyConfig)
    relation_types: RelationTypesConfig = field(default_factory=RelationTypesConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)
    custom_hooks: list[CustomHookConfig] = field(default_factory=list)

    def is_strict(self) -> bool:
        """Check if strictness is strict."""
        return self.strictness == "strict"

    def is_balanced(self) -> bool:
        """Check if strictness is balanced."""
        return self.strictness == "balanced"

    def is_flexible(self) -> bool:
        """Check if strictness is flexible."""
        return self.strictness == "flexible"
