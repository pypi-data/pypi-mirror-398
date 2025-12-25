# Agent Guide

This document explains how to work within this repository structure. Read this before starting any task.

## Repository Layout

```
├── context/          # Reference materials (not in git)
├── plans/            # Project plans and prompts
├── messages/         # Agent communication (not in git, except README)
├── AGENTS.md         # This file
├── CLAUDE.md         # Claude-specific instructions
└── README.md         # Human-readable overview
```

## Working with Context

The `context/` directory contains reference materials the user has provided. Check it at the start of each session:

1. List the directory contents
2. Read files relevant to your task
3. Use this information to inform your work

Context files are temporary. Don't assume they'll exist in future sessions.

## Working with Plans

Plans live in `plans/`. Each project has its own folder:

```
plans/my-feature/
├── README.md         # Plan overview
└── prompts/          # Executable prompts
    ├── 01-first.md
    └── 02-second.md
```

### Executing a Plan

1. Read the project README to understand scope
2. Work through prompts in order
3. Complete each prompt fully before the next
4. If blocked, post to `messages/` and continue if possible

### Creating a Plan

When the user asks you to plan work:

1. Create a folder in `plans/` with a descriptive name
2. Write a README with goal, approach, and acceptance criteria
3. Break the work into numbered prompts in a `prompts/` subfolder
4. Each prompt should be a standalone task

## Working with Messages

The `messages/` directory is for agent-to-agent communication.

### Check for Messages

At session start:
1. List `messages/` contents
2. Read any open messages
3. Respond if you can help resolve something

### Post a Message

When you have a question or are blocked:
1. Create a file: `question-topic.md` or `blocked-topic.md`
2. Describe what you need
3. Check back later for responses

### Resolve Messages

When your question is answered or blocker is cleared:
1. Delete the message file
2. Keep this directory clean

## Multi-Agent Coordination

When multiple agents work on the same codebase:

### Before Starting Work
- Check `messages/` for relevant open items
- Read any active plans in `plans/`
- Look at recent git commits to see what others have done

### During Work
- Post blockers immediately
- Share information others might need
- Don't duplicate work another agent is doing

### Handoffs
When passing work to another agent:
1. Commit your changes
2. Update the plan README with progress
3. Post a message summarizing state and next steps

## File Conventions

### What Goes in Git
- All source code
- `plans/` (all files)
- `AGENTS.md`, `CLAUDE.md`, `README.md`
- `context/README.md`, `messages/README.md`

### What Stays Local
- `context/*` (except README)
- `messages/*` (except README)

## Session Checklist

Start of session:
- [ ] Check `messages/` for open items
- [ ] Check `context/` for reference materials
- [ ] Review active plans if continuing previous work

End of session:
- [ ] Commit completed work
- [ ] Update plan progress if applicable
- [ ] Post handoff message if work continues
- [ ] Delete any resolved messages you posted
