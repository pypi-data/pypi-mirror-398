"""Validation hooks."""

import re

from basic_memory_hooks.hook import Hook
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


class ValidateFrontmatterHook(Hook):
    """Validate YAML frontmatter has required fields."""

    @property
    def name(self) -> str:
        return "validate_frontmatter"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.FIRST

    def execute(self, context: HookContext) -> HookResult:
        errors: list[str] = []

        # Check for frontmatter
        if not context.content.startswith("---"):
            errors.append("Missing YAML frontmatter")
            return HookResult(success=False, errors=errors)

        # Extract frontmatter
        match = re.match(r"^---\n(.*?)\n---", context.content, re.DOTALL)
        if not match:
            errors.append("Invalid YAML frontmatter format")
            return HookResult(success=False, errors=errors)

        frontmatter = match.group(1)

        # Check required fields
        for field in self.config.quality.require_frontmatter:
            pattern = rf"^{field}:"
            if not re.search(pattern, frontmatter, re.MULTILINE):
                errors.append(f"Frontmatter missing required field: {field}")

        return HookResult(success=len(errors) == 0, errors=errors)


class ValidateMinimumObservationsHook(Hook):
    """Validate note has minimum number of observations."""

    @property
    def name(self) -> str:
        return "validate_minimum_observations"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        # Find observations section
        obs_match = re.search(
            r"^## Observations\s*\n(.*?)(?=^## |\Z)",
            context.content,
            re.MULTILINE | re.DOTALL,
        )

        if not obs_match:
            return HookResult(
                success=False,
                errors=[f"Missing ## Observations section"],
            )

        observations_text = obs_match.group(1)

        # Count observations (lines starting with - [)
        observations = re.findall(r"^- \[", observations_text, re.MULTILINE)
        count = len(observations)
        minimum = self.config.quality.minimum_observations

        if count < minimum:
            return HookResult(
                success=False,
                errors=[f"Insufficient observations: {count} < {minimum} required"],
            )

        return HookResult(success=True)


class ValidateNoteTypeHook(Hook):
    """Validate note type is in allowed list."""

    @property
    def name(self) -> str:
        return "validate_note_type"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        # Extract type from frontmatter
        match = re.search(r"^type:\s*(.+)$", context.content, re.MULTILINE)

        if not match:
            # No type specified, will use default
            return HookResult(success=True)

        note_type = match.group(1).strip()
        allowed = self.config.note_types.allowed

        if note_type not in allowed:
            return HookResult(
                success=False,
                errors=[f"Invalid note type '{note_type}'. Allowed: {', '.join(allowed)}"],
            )

        return HookResult(success=True)


class ValidateObservationCategoriesHook(Hook):
    """Validate required observation categories are present."""

    @property
    def name(self) -> str:
        return "validate_observation_categories"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        # Find observations section
        obs_match = re.search(
            r"^## Observations\s*\n(.*?)(?=^## |\Z)",
            context.content,
            re.MULTILINE | re.DOTALL,
        )

        if not obs_match:
            return HookResult(success=True)  # Handled by other hook

        observations_text = obs_match.group(1)

        # Extract categories used
        categories_used = set(re.findall(r"- \[(\w+)\]", observations_text))

        # Check required categories
        required = set(self.config.observation_categories.required)
        missing = required - categories_used

        if missing:
            return HookResult(
                success=False,
                errors=[f"Missing required observation categories: {', '.join(sorted(missing))}"],
            )

        # Check for invalid categories
        all_valid = required | set(self.config.observation_categories.optional)
        invalid = categories_used - all_valid

        if invalid:
            return HookResult(
                success=False,
                errors=[f"Invalid observation categories: {', '.join(sorted(invalid))}"],
            )

        return HookResult(success=True)


class ValidateTagPrefixesHook(Hook):
    """Validate tags use required prefixes (if enforced)."""

    @property
    def name(self) -> str:
        return "validate_tag_prefixes"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def should_run(self, context: HookContext) -> bool:
        # Only run if prefix enforcement is enabled
        return self.config.tag_taxonomy.enforce

    def execute(self, context: HookContext) -> HookResult:
        # Extract tags from frontmatter
        match = re.search(
            r"^tags:\s*\n((?:- .+\n)*)", context.content, re.MULTILINE
        )

        if not match:
            return HookResult(success=True)

        tags_text = match.group(1)
        tags = re.findall(r"^- (.+)$", tags_text, re.MULTILINE)

        # Check prefixes
        valid_prefixes = set(self.config.tag_taxonomy.prefixes.keys())
        invalid_tags = []

        for tag in tags:
            tag = tag.strip()
            # Check if tag has a valid prefix
            has_valid_prefix = any(tag.startswith(f"{prefix}/") for prefix in valid_prefixes)
            if not has_valid_prefix:
                invalid_tags.append(tag)

        if invalid_tags:
            return HookResult(
                success=False,
                errors=[
                    f"Tags missing required prefix: {', '.join(invalid_tags)}. "
                    f"Valid prefixes: {', '.join(sorted(valid_prefixes))}"
                ],
            )

        return HookResult(success=True)


class VerifyRelationTargetsHook(Hook):
    """Verify relation targets exist (POST_WRITE hook)."""

    @property
    def name(self) -> str:
        return "verify_relation_targets"

    @property
    def stage(self) -> HookStage:
        return HookStage.POST_WRITE

    def execute(self, context: HookContext) -> HookResult:
        # Find relations section
        rel_match = re.search(
            r"^## Relations\s*\n(.*?)(?=^## |\Z)",
            context.content,
            re.MULTILINE | re.DOTALL,
        )

        if not rel_match:
            return HookResult(success=True)

        relations_text = rel_match.group(1)

        # Extract relation targets
        targets = re.findall(r"\[\[([^\]]+)\]\]", relations_text)

        # For now, just note the targets - actual verification would need
        # access to the knowledge base, which is handled by the caller
        if targets:
            return HookResult(
                success=True,
                metadata={"relation_targets": targets},
                warnings=[f"Relation targets to verify: {', '.join(targets)}"]
                if not self.config.quality.allow_forward_references
                else [],
            )

        return HookResult(success=True)
