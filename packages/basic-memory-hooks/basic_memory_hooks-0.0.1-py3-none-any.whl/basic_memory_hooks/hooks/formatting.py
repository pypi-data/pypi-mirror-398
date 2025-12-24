"""Formatting hooks."""

import re

from basic_memory_hooks.hook import Hook
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


class RemoveDuplicateHeadingsHook(Hook):
    """Remove duplicate section headings (common LLM artifact)."""

    @property
    def name(self) -> str:
        return "remove_duplicate_headings"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.HIGH

    # Sections handled by specialized consolidation hooks - don't remove these
    CONSOLIDATION_SECTIONS = {"Observations", "Relations"}

    def execute(self, context: HookContext) -> HookResult:
        content = context.content
        lines = content.split("\n")
        result_lines = []
        seen_headings: set[str] = set()
        duplicates_removed = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this is a heading (## or ###)
            heading_match = re.match(r"^(#{2,3})\s+(.+)$", line)
            if heading_match:
                heading_text = heading_match.group(2).strip()

                # Skip sections with specialized consolidation hooks
                if heading_text in self.CONSOLIDATION_SECTIONS:
                    seen_headings.add(heading_text)
                    result_lines.append(line)
                    i += 1
                    continue

                if heading_text in seen_headings:
                    # Skip this duplicate heading and its content until next heading
                    duplicates_removed += 1
                    i += 1
                    # Skip content until next heading or end
                    while i < len(lines) and not re.match(r"^#{2,3}\s+", lines[i]):
                        i += 1
                    continue
                else:
                    seen_headings.add(heading_text)

            result_lines.append(line)
            i += 1

        new_content = "\n".join(result_lines)

        return HookResult(
            success=True,
            content=new_content if duplicates_removed > 0 else None,
            metadata={"duplicates_removed": duplicates_removed},
        )


class ConsolidateObservationsHook(Hook):
    """Merge multiple Observations sections into one."""

    @property
    def name(self) -> str:
        return "consolidate_observations"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.HIGH

    def execute(self, context: HookContext) -> HookResult:
        content = context.content

        # Find all Observations sections
        pattern = r"^## Observations\s*\n(.*?)(?=^## |\Z)"
        matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

        if len(matches) <= 1:
            return HookResult(success=True)

        # Collect all observations
        all_observations: list[str] = []
        for match in matches:
            obs_content = match.group(1).strip()
            # Extract individual observations
            obs_lines = [
                line for line in obs_content.split("\n") if line.strip().startswith("- ")
            ]
            all_observations.extend(obs_lines)

        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_observations: list[str] = []
        for obs in all_observations:
            if obs not in seen:
                seen.add(obs)
                unique_observations.append(obs)

        # Build consolidated section
        consolidated = "## Observations\n" + "\n".join(unique_observations)

        # Remove all Observations sections from content
        new_content = re.sub(
            r"^## Observations\s*\n.*?(?=^## |\Z)",
            "",
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        # Find where to insert consolidated section (after frontmatter and any intro)
        # Look for first ## heading
        first_heading = re.search(r"^## ", new_content, re.MULTILINE)
        if first_heading:
            insert_pos = first_heading.start()
            new_content = (
                new_content[:insert_pos] + consolidated + "\n\n" + new_content[insert_pos:]
            )
        else:
            # No headings, append at end
            new_content = new_content.rstrip() + "\n\n" + consolidated + "\n"

        return HookResult(
            success=True,
            content=new_content,
            metadata={"sections_consolidated": len(matches)},
        )


class FormatObservationsHook(Hook):
    """Ensure observations follow the - [category] content format."""

    @property
    def name(self) -> str:
        return "format_observations"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        content = context.content

        # Find observations section
        obs_match = re.search(
            r"(^## Observations\s*\n)(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not obs_match:
            return HookResult(success=True)

        obs_header = obs_match.group(1)
        obs_content = obs_match.group(2)
        obs_start = obs_match.start()
        obs_end = obs_match.end()

        # Process each line in observations
        lines = obs_content.split("\n")
        fixed_lines: list[str] = []
        fixes_made = 0

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                continue

            # Check if it's already properly formatted (- [category] text, not - [category]: text)
            if re.match(r"^- \[\w+\] ", stripped):
                fixed_lines.append(line)
                continue

            # Try to fix common issues
            # Case: "- category: content" -> "- [category] content"
            cat_match = re.match(r"^-\s+(\w+):\s+(.+)$", stripped)
            if cat_match:
                category = cat_match.group(1).lower()
                obs_text = cat_match.group(2)
                fixed_lines.append(f"- [{category}] {obs_text}")
                fixes_made += 1
                continue

            # Case: "- [category]: content" -> "- [category] content"
            colon_match = re.match(r"^-\s+\[(\w+)\]:\s+(.+)$", stripped)
            if colon_match:
                category = colon_match.group(1).lower()
                obs_text = colon_match.group(2)
                fixed_lines.append(f"- [{category}] {obs_text}")
                fixes_made += 1
                continue

            # Case: bullet without category, use default
            if stripped.startswith("- "):
                obs_text = stripped[2:].strip()
                default_cat = self.config.note_types.default
                fixed_lines.append(f"- [{default_cat}] {obs_text}")
                fixes_made += 1
                continue

            # Keep line as-is if we can't parse it
            fixed_lines.append(line)

        if fixes_made == 0:
            return HookResult(success=True)

        new_obs_content = obs_header + "\n".join(fixed_lines)
        new_content = content[:obs_start] + new_obs_content + content[obs_end:]

        return HookResult(
            success=True,
            content=new_content,
            metadata={"observations_fixed": fixes_made},
        )


class OrderRelationsHook(Hook):
    """Order relations with primary types before secondary types."""

    @property
    def name(self) -> str:
        return "order_relations"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        content = context.content

        # Find relations section
        rel_match = re.search(
            r"(^## Relations\s*\n)(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not rel_match:
            return HookResult(success=True)

        rel_header = rel_match.group(1)
        rel_content = rel_match.group(2)
        rel_start = rel_match.start()
        rel_end = rel_match.end()

        # Parse relations
        lines = rel_content.split("\n")
        primary_relations: list[str] = []
        secondary_relations: list[str] = []
        other_lines: list[str] = []

        primary_types = set(self.config.relation_types.primary)
        secondary_types = set(self.config.relation_types.secondary)

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            # Check if it's a relation line
            rel_line_match = re.match(r"^-\s+(\w+)\s+\[\[", stripped)
            if rel_line_match:
                rel_type = rel_line_match.group(1)
                if rel_type in primary_types:
                    primary_relations.append(line)
                elif rel_type in secondary_types:
                    secondary_relations.append(line)
                else:
                    other_lines.append(line)
            else:
                other_lines.append(line)

        # Check if already in correct order
        original_order = [
            line for line in lines if line.strip() and line.strip().startswith("- ")
        ]
        new_order = primary_relations + secondary_relations + other_lines

        if original_order == new_order:
            return HookResult(success=True)

        # Build new relations section
        new_rel_content = rel_header + "\n".join(new_order) + "\n"
        new_content = content[:rel_start] + new_rel_content + content[rel_end:]

        return HookResult(
            success=True,
            content=new_content,
            metadata={"relations_reordered": True},
        )
