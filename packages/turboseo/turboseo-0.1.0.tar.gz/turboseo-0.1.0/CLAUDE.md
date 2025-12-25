# Claude Instructions

This file contains instructions for Claude when working in this repository. It supplements `AGENTS.md` with Claude-specific guidance.

## First Steps

When starting a session:

1. **Check messages** - Read `messages/` for any open questions or blockers
2. **Check context** - Look in `context/` for reference materials
3. **Understand the task** - Ask clarifying questions if the request is ambiguous

## Directory Quick Reference

| Directory | Purpose | In Git? |
|-----------|---------|---------|
| `context/` | User-provided reference files | No (except README) |
| `plans/` | Project plans and prompts | Yes |
| `messages/` | Agent communication | No (except README) |

## Planning Work

When asked to plan a feature or project:

1. Create a folder in `plans/` with a clear name
2. Write a README with:
   - Goal
   - Background (if needed)
   - Approach
   - Acceptance criteria
3. Create a `prompts/` subfolder
4. Write numbered prompt files (01-, 02-, etc.)

Each prompt should be self-contained. Another agent (or a future session) should be able to execute it without additional context.

## Executing Plans

When working from an existing plan:

1. Read the plan README first
2. Execute prompts in order
3. If blocked, post to `messages/` and skip to the next prompt if possible
4. Update the plan README with progress notes

## Communication

### Asking Questions

If you need information from another agent or the user:

```markdown
# Question: [Topic]

**From**: Claude
**Date**: [Current date/time]
**Status**: Open

## Question

[Your question here]
```

Save as `messages/question-topic.md`.

### Reporting Blockers

If you cannot proceed:

```markdown
# Blocked: [Topic]

**From**: Claude
**Date**: [Current date/time]
**Status**: Open

## Blocker

[What's blocking you]

## Attempted

[What you tried]

## Needed

[What would unblock you]
```

Save as `messages/blocked-topic.md`.

### Cleanup

Delete your messages from `messages/` once resolved.

## Code Style

Follow existing patterns in the codebase. If no patterns exist yet:

- Write clear, readable code
- Add comments only where the logic isn't obvious
- Prefer simple solutions over clever ones

## Commits

When asked to commit:

- Write concise commit messages
- Focus on what changed and why
- Group related changes together
