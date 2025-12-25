# Plans Directory

This directory contains project plans. Each project gets its own folder with a structured breakdown of what needs to be built and the prompts to build it.

## Structure

```
plans/
├── README.md (this file)
├── feature-user-auth/
│   ├── README.md (plan overview)
│   └── prompts/
│       ├── 01-database-schema.md
│       ├── 02-api-endpoints.md
│       └── 03-frontend-forms.md
└── bugfix-checkout-flow/
    ├── README.md
    └── prompts/
        └── 01-fix-validation.md
```

## Creating a New Plan

### 1. Create a project folder

Name it descriptively: `feature-`, `bugfix-`, `refactor-`, or similar prefix helps identify the work type.

### 2. Write the plan README

The project README should contain:

- **Goal**: What you're building or fixing
- **Background**: Why this work is needed
- **Scope**: What's included and what's not
- **Approach**: High-level strategy
- **Dependencies**: What needs to exist first
- **Acceptance criteria**: How to know when it's done

### 3. Create the prompts directory

Break the work into sequential prompts. Each prompt file should be a self-contained task that an agent can execute. Number them to indicate order.

## Writing Prompts

A prompt file should include:

```markdown
# Task Title

## Context
What the agent needs to know before starting.

## Task
The specific work to complete.

## Constraints
Any limitations or requirements.

## Output
What the agent should produce.
```

## For Agents

When working from a plan:

1. Read the project README first to understand the full scope
2. Execute prompts in numbered order
3. Complete each prompt before moving to the next
4. If a prompt is blocked, document the blocker in `/messages` and move on if possible
5. Update the plan README with progress notes if the plan spans multiple sessions

## Archiving Completed Plans

When a plan is finished, either:
- Delete the folder if the prompts have no reuse value
- Move to an `archive/` subfolder if you want to keep them for reference
