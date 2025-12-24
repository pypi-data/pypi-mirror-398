"""Standard hooks for Basic Memory Hooks."""

from basic_memory_hooks.hooks.validation import (
    ValidateFrontmatterHook,
    ValidateMinimumObservationsHook,
    ValidateNoteTypeHook,
    ValidateObservationCategoriesHook,
    ValidateTagPrefixesHook,
    VerifyRelationTargetsHook,
)
from basic_memory_hooks.hooks.formatting import (
    RemoveDuplicateHeadingsHook,
    ConsolidateObservationsHook,
    FormatObservationsHook,
    OrderRelationsHook,
)


def get_standard_hooks() -> list[type]:
    """Get all standard hook classes."""
    return [
        # PRE_WRITE - FIRST priority
        ValidateFrontmatterHook,
        # PRE_WRITE - HIGH priority
        RemoveDuplicateHeadingsHook,
        ConsolidateObservationsHook,
        # PRE_WRITE - NORMAL priority
        FormatObservationsHook,
        ValidateMinimumObservationsHook,
        ValidateNoteTypeHook,
        ValidateObservationCategoriesHook,
        ValidateTagPrefixesHook,
        OrderRelationsHook,
        # POST_WRITE - NORMAL priority
        VerifyRelationTargetsHook,
    ]


__all__ = [
    "ValidateFrontmatterHook",
    "ValidateMinimumObservationsHook",
    "ValidateNoteTypeHook",
    "ValidateObservationCategoriesHook",
    "ValidateTagPrefixesHook",
    "VerifyRelationTargetsHook",
    "RemoveDuplicateHeadingsHook",
    "ConsolidateObservationsHook",
    "FormatObservationsHook",
    "OrderRelationsHook",
    "get_standard_hooks",
]
