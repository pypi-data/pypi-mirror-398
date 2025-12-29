#!/bin/bash
#
# HtmlGraph Pre-Commit Hook
# 1. BLOCKS direct edits to .htmlgraph/ (AI agents must use SDK)
# 2. Reminds developers to create/start features for non-trivial work
#
# To disable feature reminder: git config htmlgraph.precommit false
# To bypass blocking once: git commit --no-verify (NOT RECOMMENDED)

# Check if HtmlGraph is initialized
if [ ! -d ".htmlgraph" ]; then
    # Not an HtmlGraph project, skip silently
    exit 0
fi

# Redirect output to stderr (standard for git hooks)
exec 1>&2

# ============================================================
# BLOCKING CHECK: Direct edits to .htmlgraph/ files
# AI agents must use SDK, not direct file edits
# ============================================================
HTMLGRAPH_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep "^\\.htmlgraph/" || true)

if [ -n "$HTMLGRAPH_FILES" ]; then
    echo ""
    echo "❌ BLOCKED: Direct edits to .htmlgraph/ files"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Modified files:"
    echo "$HTMLGRAPH_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    echo "AI agents must use SDK, not direct file edits."
    echo "See AGENTS.md line 3: 'AI agents must NEVER edit .htmlgraph/ HTML files directly'"
    echo ""
    echo "Use SDK instead:"
    echo "  from htmlgraph import SDK"
    echo "  sdk = SDK()"
    echo "  sdk.features.complete('feature-id')  # Mark feature done"
    echo "  sdk.features.create('Title')         # Create new feature"
    echo ""
    echo "Or CLI:"
    echo "  uv run htmlgraph feature complete <id>"
    echo "  uv run htmlgraph feature create 'Title'"
    echo ""
    echo "To bypass (NOT RECOMMENDED): git commit --no-verify"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi

# ============================================================
# REMINDER CHECK: Feature tracking (non-blocking)
# ============================================================
# Check if reminder is disabled via config
if [ "$(git config --type=bool htmlgraph.precommit)" = "false" ]; then
    exit 0
fi

# Fast check for in-progress features using grep (avoids Python startup)
ACTIVE_COUNT=$(find .htmlgraph/features -name "*.html" -exec grep -l 'data-status="in-progress"' {} \; 2>/dev/null | wc -l | tr -d ' ')

# If we have active features and htmlgraph CLI is available, get details
if [ "$ACTIVE_COUNT" -gt 0 ] && command -v htmlgraph &> /dev/null; then
    ACTIVE_FEATURES=$(htmlgraph feature list --status in-progress 2>/dev/null)
else
    ACTIVE_FEATURES=""
fi

if [ "$ACTIVE_COUNT" -gt 0 ]; then
    echo ""
    echo "✓ HtmlGraph: $ACTIVE_COUNT active feature(s)"
    echo ""
    echo "$ACTIVE_FEATURES"
    echo ""
else
    echo ""
    echo "⚠️  HtmlGraph Feature Reminder"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "No active features found. Did you forget to start one?"
    echo ""
    echo "Quick decision:"
    echo "  • >30 min work? → Create feature"
    echo "  • 3+ files? → Create feature"
    echo "  • Simple fix? → Direct commit OK"
    echo ""
    echo "To disable: git config htmlgraph.precommit false"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

exit 0
