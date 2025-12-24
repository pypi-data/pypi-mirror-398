"""Custom hook to validate hook-related concepts in observations.

This is a sample custom hook that demonstrates:
1. Extending the Hook base class
2. Using should_run() for conditional execution
3. Returning warnings for non-fatal issues
"""

import re

from basic_memory_hooks.hook import Hook
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


class ValidateHookConceptsHook(Hook):
    """Validate that hook-related observations use correct terminology."""

    # Terms that suggest confusion (with corrections)
    CONFUSED_TERMS = {
        "pre-write": "pre_write",
        "post-write": "post_write",
        "prewrite": "pre_write",
        "postwrite": "post_write",
    }

    @property
    def name(self) -> str:
        return "validate_hook_concepts"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.LOW  # Run after formatting

    def should_run(self, context: HookContext) -> bool:
        """Only run on content that discusses hooks."""
        content_lower = context.content.lower()
        return "hook" in content_lower or "stage" in content_lower

    def execute(self, context: HookContext) -> HookResult:
        content = context.content
        warnings: list[str] = []

        # Find observations section
        obs_match = re.search(
            r"^## Observations\s*\n(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not obs_match:
            return HookResult(success=True)

        obs_content = obs_match.group(1)

        # Check for confused terminology
        for wrong, correct in self.CONFUSED_TERMS.items():
            if wrong in obs_content.lower():
                warnings.append(
                    f"Consider using '{correct}' instead of '{wrong}' for consistency"
                )

        return HookResult(
            success=True,
            warnings=warnings,
            metadata={"hook_concepts_checked": True},
        )
