# Messages Directory

This is the communication channel between agents. Use it to ask questions, flag blockers, and coordinate work when multiple agents operate on the same codebase.

## How It Works

Agents write messages as markdown files. Other agents check this directory and respond. When a message is resolved, delete it.

## Message Format

Create a file with a descriptive name: `question-api-auth.md`, `blocked-database-migration.md`, etc.

```markdown
# [Question/Blocked/Info]: Brief Title

**From**: Agent identifier or session ID
**Date**: YYYY-MM-DD HH:MM
**Status**: Open

## Message

Your question or information here.

---

## Responses

(Other agents add responses below)

### Response from [Agent]
**Date**: YYYY-MM-DD HH:MM

Response content here.
```

## Message Types

### Questions
Use when you need input from another agent or the user.

```
question-auth-strategy.md
question-which-database.md
```

### Blockers
Use when you cannot proceed without resolution.

```
blocked-missing-api-key.md
blocked-failing-tests.md
```

### Info
Use to share information other agents might need.

```
info-schema-changed.md
info-new-endpoints.md
```

## For Agents

### Posting a Message

1. Create a markdown file in this directory
2. Use the format above
3. Be specific about what you need

### Checking Messages

1. List files in this directory at the start of your session
2. Read any open messages relevant to your work
3. Respond if you can help

### Resolving Messages

When a message is resolved:
1. The original poster deletes the file
2. If you resolved someone else's question, add your response and let them delete it

## Cleanup

This directory should stay clean. Messages are temporary coordination tools, not permanent records. Delete resolved messages promptly.

Files here (except this README) are excluded from version control.
