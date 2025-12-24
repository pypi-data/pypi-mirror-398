# SPEC-0: How to Write Specs

## Why

Specifications solve the complexity and circular refactoring issues in development. Instead of getting lost in implementation details, we start with clear specifications that drive implementation.

Ad-hoc development with AI agents tends to result in:
- Circular refactoring cycles
- Fighting framework complexity
- Lost context between sessions
- Unclear requirements and scope

Specs are **complete thoughts** that provide:
- Clear reasoning for decisions
- Actionable implementation guidance
- Testable success criteria
- Historical context for future reference

## What

This document defines how to write specifications for the basic-memory-hooks project. All specs live in `docs/specs/` and follow a consistent format.

## How (High Level)

### Spec Naming

Specs are numbered sequentially:
```
SPEC-0-how-to-write-specs.md
SPEC-1-configuration-schema.md
SPEC-2-hook-system-interface.md
```

Use lowercase with hyphens. The number comes first for sorting.

### Spec Template

Every spec contains these sections:

```markdown
# SPEC-X: Title

## Why

The problem being solved. What's broken or missing?
Why does this matter?

## What

What is affected or changed. Scope and boundaries.
What is NOT included (if helpful to clarify).

## How (High Level)

Approach to implementation. Key decisions and trade-offs.
Code examples, diagrams, or API definitions as needed.

## How to Evaluate

### Success Criteria
- [ ] Specific, testable criteria
- [ ] Each criterion is pass/fail

### Test Cases
- Scenario → Expected outcome
```

### Living Documents

Specs evolve throughout implementation. Track progress with checkboxes:

```markdown
### Feature X
- ✅ Basic functionality implemented
- [x] Currently implementing edge cases
- [ ] Add error handling
- [ ] Write tests
```

**Progress markers:**
- `✅` — Completed and verified
- `[x]` — In progress
- `[ ]` — Not started

Avoid static status headers like "COMPLETE" or "IN PROGRESS" that become stale. Let the checkboxes tell the story.

### What Makes a Good Spec

**Start with Why.** If you can't explain why something matters, you're not ready to spec it.

**Be specific.** "Improve performance" is not a spec. "Reduce API response time to under 100ms for validation requests" is.

**Include examples.** Code snippets, JSON payloads, CLI invocations. Show, don't just tell.

**Define success.** How do we know when we're done? What can we test?

**Keep it focused.** One spec = one complete thought. If it's getting long, split it.

### When to Write a Spec

Write a spec when:
- Adding a new feature or component
- Making an architectural decision
- Changing behavior that affects users
- You need to think through a complex problem

Skip the spec when:
- Fixing a simple bug
- Making a trivial change
- The implementation is obvious and small

### Updating Specs

Specs record history. When implementation diverges from the spec:

1. Update the spec to reflect what actually happened
2. Note why the change was made
3. Keep the "How to Evaluate" criteria accurate

A spec that doesn't match reality is worse than no spec.

## How to Evaluate

### Success Criteria
- [ ] New specs follow the template structure
- [ ] Specs are discoverable in `docs/specs/`
- [ ] Specs provide actionable guidance for implementation
- [ ] Specs record decisions and their reasoning
- [ ] Progress is trackable via checkboxes

### Test Cases
- New feature → Spec written before implementation begins
- Spec review → Implementation matches success criteria
- Historical lookup → Past decisions are findable and understandable
