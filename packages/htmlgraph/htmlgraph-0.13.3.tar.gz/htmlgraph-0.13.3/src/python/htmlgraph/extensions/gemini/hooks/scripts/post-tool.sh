#!/bin/bash
#
# HtmlGraph AfterTool Hook for Gemini CLI
# Tracks tool usage for activity attribution
#

set +e

# Find project root
PROJECT_ROOT="$(pwd)"

# Check if .htmlgraph exists
if [ ! -d "$PROJECT_ROOT/.htmlgraph" ]; then
  exit 0  # Not an HtmlGraph project
fi

# Read hook input from stdin (Gemini passes JSON)
INPUT=$(cat)

# Extract tool name from JSON (basic parsing)
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOOL_NAME" ]; then
  exit 0  # No tool name, skip
fi

# Check if htmlgraph is installed
if ! command -v htmlgraph &> /dev/null; then
  if ! command -v uv &> /dev/null; then
    exit 0
  fi
  HTMLGRAPH_CMD="uv run htmlgraph"
else
  HTMLGRAPH_CMD="htmlgraph"
fi

export HTMLGRAPH_AGENT=gemini

# Track the tool usage event
$HTMLGRAPH_CMD activity "$TOOL_NAME" "Tool used: $TOOL_NAME" &> /dev/null &

exit 0
