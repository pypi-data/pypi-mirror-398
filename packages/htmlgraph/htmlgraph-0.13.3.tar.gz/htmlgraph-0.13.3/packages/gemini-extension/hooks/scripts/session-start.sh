#!/bin/bash
#
# HtmlGraph SessionStart Hook for Gemini CLI
# Initializes HtmlGraph session tracking and provides feature awareness
#

set +e

# Find project root (where .htmlgraph might be)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"

# Check if .htmlgraph exists
if [ ! -d "$PROJECT_ROOT/.htmlgraph" ]; then
  exit 0  # Not an HtmlGraph project, skip silently
fi

# Check if htmlgraph is installed
if ! command -v htmlgraph &> /dev/null; then
  # Try with uv run
  if ! command -v uv &> /dev/null; then
    exit 0  # Can't run htmlgraph, skip
  fi
  HTMLGRAPH_CMD="uv run htmlgraph"
else
  HTMLGRAPH_CMD="htmlgraph"
fi

export HTMLGRAPH_AGENT=gemini

# Get comprehensive session start info (includes status, recommendations, conflicts, etc.)
SESSION_START_INFO=$($HTMLGRAPH_CMD session start-info 2>/dev/null)

# If session start-info is not available, fall back to basic status
if [ $? -ne 0 ] || [ -z "$SESSION_START_INFO" ]; then
  # Start a new session (or resume if one exists)
  SESSION_ID=$($HTMLGRAPH_CMD session start --agent gemini 2>/dev/null | grep -o 'session-[a-z0-9-]*' | head -1)

  if [ -z "$SESSION_ID" ]; then
    # Try to get active session
    SESSION_ID=$($HTMLGRAPH_CMD session list 2>/dev/null | grep -o 'session-[a-z0-9-]*' | head -1)
  fi

  # Get current status
  STATUS_OUTPUT=$($HTMLGRAPH_CMD status 2>/dev/null)

  # Get latest handoff context (if any)
  HANDOFF_CONTEXT=$($HTMLGRAPH_CMD session handoff --show 2>/dev/null)
  HANDOFF_SECTION=""
  if [ -n "$HANDOFF_CONTEXT" ] && [[ "$HANDOFF_CONTEXT" != "No handoff context found."* ]]; then
    HANDOFF_SECTION=$(cat <<EOF

## Handoff Context

$HANDOFF_CONTEXT

---
EOF
)
  fi
fi

# Build context message for Gemini
if [ -n "$SESSION_START_INFO" ]; then
  # Use enhanced session start info
  cat <<EOF

---

## HTMLGRAPH DEVELOPMENT PROCESS ACTIVE

**CRITICAL: HtmlGraph is tracking this session. Read GEMINI.md for complete instructions.**

### Feature Creation Decision Framework

**Use this framework for EVERY user request:**

Create a **FEATURE** if ANY apply:
- >30 minutes work
- 3+ files
- New tests needed
- Multi-component impact
- Hard to revert
- Needs docs

Implement **DIRECTLY** if ALL apply:
- Single file
- <30 minutes
- Trivial change
- Easy to revert
- No tests needed

**When in doubt, CREATE A FEATURE.** Over-tracking is better than losing attribution.

---

### Quick Reference

**IMPORTANT:** Always use \`uv run\` when running htmlgraph commands.

**Check Status:**
\`\`\`bash
uv run htmlgraph status
uv run htmlgraph feature list
uv run htmlgraph session list
\`\`\`

**Work Item Commands:**
- \`uv run htmlgraph feature start <id>\` - Start working on a feature
- \`uv run htmlgraph feature complete <id>\` - Mark feature as done

**Dashboard:**
\`\`\`bash
uv run htmlgraph serve
# Open http://localhost:8080
\`\`\`

---

$SESSION_START_INFO

---

## Session Continuity

HtmlGraph is tracking all activity to this session. Activities are automatically attributed to in-progress features.

**REMEMBER:**
1. Start features before coding: \`uv run htmlgraph feature start <id>\`
2. Mark steps complete immediately using SDK
3. Complete features when done: \`uv run htmlgraph feature complete <id>\`

See GEMINI.md for complete workflow and SDK usage instructions.

EOF
else
  # Fall back to basic status
  cat <<EOF

---

## HTMLGRAPH DEVELOPMENT PROCESS ACTIVE

**CRITICAL: HtmlGraph is tracking this session. Read GEMINI.md for complete instructions.**

### Feature Creation Decision Framework

**Use this framework for EVERY user request:**

Create a **FEATURE** if ANY apply:
- >30 minutes work
- 3+ files
- New tests needed
- Multi-component impact
- Hard to revert
- Needs docs

Implement **DIRECTLY** if ALL apply:
- Single file
- <30 minutes
- Trivial change
- Easy to revert
- No tests needed

**When in doubt, CREATE A FEATURE.** Over-tracking is better than losing attribution.

---

### Quick Reference

**IMPORTANT:** Always use \`uv run\` when running htmlgraph commands.

**Check Status:**
\`\`\`bash
uv run htmlgraph status
uv run htmlgraph feature list
uv run htmlgraph session list
\`\`\`

**Work Item Commands:**
- \`uv run htmlgraph feature start <id>\` - Start working on a feature
- \`uv run htmlgraph feature complete <id>\` - Mark feature as done

**Dashboard:**
\`\`\`bash
uv run htmlgraph serve
# Open http://localhost:8080
\`\`\`

---

## Project Status

$STATUS_OUTPUT

---
$HANDOFF_SECTION

## Session Continuity

**Session ID:** $SESSION_ID

HtmlGraph is tracking all activity to this session. Activities are automatically attributed to in-progress features.

**REMEMBER:**
1. Start features before coding: \`uv run htmlgraph feature start <id>\`
2. Mark steps complete immediately using SDK
3. Complete features when done: \`uv run htmlgraph feature complete <id>\`

See GEMINI.md for complete workflow and SDK usage instructions.

EOF
fi

exit 0
