# SPEC-1: Configuration Schema

## Why

Basic Memory Hooks needs a configuration format that is machine-parseable, lives with project data, and syncs via Basic Memory Cloud.

## What

- Configuration file: `.basic-memory/format.md`
- Config stored in YAML frontmatter (merged with Basic Memory's standard fields)
- Body can contain optional documentation

## How (High Level)

### File Format

```yaml
---
title: format
type: config
permalink: .basic-memory/format
version: "1.0"
strictness: balanced

note_types:
  default: note
  allowed: [note, spec, decision, meeting, person, project, research]

observation_categories:
  required: [fact, decision, technique]
  optional: [insight, question, idea, requirement, problem, solution]

tag_taxonomy:
  enforce: false
  prefixes:
    tech: "Technical topics"
    domain: "Business domains"

relation_types:
  primary: [implements, requires, part_of]
  secondary: [relates_to, extends, contrasts_with, supersedes]

quality:
  minimum_observations: 3
  minimum_relations: 1
  require_tags: true
  require_frontmatter: [title, type]
  allow_forward_references: true
  auto_fix: true

hooks:
  pre_write:
    validate_frontmatter: {enabled: true, priority: first}
    remove_duplicate_headings: {enabled: true, priority: high}
    consolidate_observations: {enabled: true, priority: high}
    format_observations: {enabled: true, priority: normal}
    validate_minimum_observations: {enabled: true, priority: normal}
    validate_note_type: {enabled: true, priority: normal}
    order_relations: {enabled: true, priority: normal}
  post_write:
    verify_relation_targets: {enabled: true, priority: normal}

custom_hooks:
  - path: hooks/project_tags.py
    enabled: true
---

Optional documentation about this project's standards.
```

### Field Specifications

#### version (required)
Type: string. Current: `"1.0"`.

#### strictness (required)
Controls validation behavior:

| Value | Behavior |
|-------|----------|
| `strict` | All hooks run, collect all errors, reject note if any errors |
| `balanced` | All hooks run, issues reported as warnings, accept note |
| `flexible` | Only formatting hooks run, no validation, accept note |

#### note_types
- `default`: Type assigned when frontmatter omits type. Default: `note`
- `allowed`: Valid type values. Default: `[note, spec, decision, meeting, person, project, research]`

#### observation_categories
- `required`: Categories expected in every note. Missing category = error (strict) or warning (balanced). Default: `[fact, decision, technique]`
- `optional`: Additional valid categories. Default: `[insight, question, idea, requirement, problem, solution]`

#### tag_taxonomy
- `enforce`: If true, tags must use defined prefixes. Non-prefixed tag = error (strict) or warning (balanced). Default: `false`
- `prefixes`: Map of prefix to description.

#### relation_types
- `primary`: Core relations. Must appear before secondary relations. Default: `[implements, requires, part_of]`
- `secondary`: Additional relations. Must appear after primary. Default: `[relates_to, extends, contrasts_with, supersedes]`

Out-of-order relations = error (strict) or warning (balanced).

#### quality
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `minimum_observations` | int | 3 | Minimum observation count |
| `minimum_relations` | int | 1 | Minimum relation count |
| `require_tags` | bool | true | Whether tags are required |
| `require_frontmatter` | list | [title, type] | Required frontmatter fields |
| `allow_forward_references` | bool | true | Allow relations to non-existent notes |
| `auto_fix` | bool | true | Hooks fix issues when possible |

#### hooks
Organized by stage. Each hook has:
- `enabled`: boolean
- `priority`: `first`, `high`, `normal`, `low`, `last`

#### custom_hooks
List of custom hook files:
- `path`: Relative to `.basic-memory/`
- `enabled`: boolean

### When format.md Doesn't Exist

All defaults apply. All notes pass validation.

### Parsing

1. Read `.basic-memory/format.md` via `read_content` (Cloud) or file read (local)
2. Parse YAML frontmatter
3. Ignore Basic Memory fields: `title`, `type`, `permalink`
4. Extract config fields, apply defaults for missing fields

## How to Evaluate

### Success Criteria
- [ ] Parser correctly extracts config from frontmatter
- [ ] Basic Memory fields (title, type, permalink) are ignored
- [ ] Missing optional fields use documented defaults
- [ ] Invalid config values produce clear errors
- [ ] Works via read_content (Cloud) and file read (local)

### Test Cases
- Minimal config (version + strictness only)
- Full config (all fields populated)
- Missing format.md (use all defaults)
- Invalid strictness value
- Invalid hook priority
