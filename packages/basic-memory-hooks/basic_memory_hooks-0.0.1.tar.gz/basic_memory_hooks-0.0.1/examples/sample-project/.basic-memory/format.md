---
title: format
type: config
version: "1.0"
strictness: balanced

note_types:
  default: memo
  allowed:
    - memo
    - spec
    - decision
    - blog
    - tutorial
    - reference

observation_categories:
  required:
    - fact
    - decision
    - technique
  optional:
    - insight
    - learning
    - pattern
    - problem
    - solution
    - example

relation_types:
  primary:
    - implements
    - requires
    - part_of
  secondary:
    - relates_to
    - extends
    - documents

quality:
  minimum_observations: 2
  minimum_relations: 1
  require_tags: true
  auto_fix: true

hooks:
  pre_write:
    validate_frontmatter:
      enabled: true
      priority: first
    remove_duplicate_headings:
      enabled: true
      priority: high
    consolidate_observations:
      enabled: true
      priority: high
    format_observations:
      enabled: true
      priority: normal
    order_relations:
      enabled: true
      priority: low

custom_hooks:
  - path: hooks/validate_hook_concepts.py
    enabled: true
---

# Format Configuration

Sample configuration for demonstrating Basic Memory Hooks.

This file lives in your project's `.basic-memory/` directory and defines:
- Allowed note types and observation categories
- Quality requirements (minimum observations, relations)
- Which hooks are enabled and their priorities
- Custom hooks to load
