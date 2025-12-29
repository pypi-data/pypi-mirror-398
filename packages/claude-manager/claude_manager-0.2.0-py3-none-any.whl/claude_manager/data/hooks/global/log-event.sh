#!/bin/bash
# Hook PreToolUse: Log des événements Task, Bash, Edit, Write
INPUT=$(cat)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR" 2>/dev/null

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)

case "$TOOL_NAME" in
  Task)
    AGENT=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // ""' 2>/dev/null)
    DESC=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null)
    echo "[$TIMESTAMP] [AGENT] $AGENT | $DESC" >> "$LOG_DIR/events.log" 2>/dev/null
    ;;
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
    echo "[$TIMESTAMP] [BASH] $CMD" >> "$LOG_DIR/events.log" 2>/dev/null
    ;;
  Edit)
    FILE=$(basename "$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)" 2>/dev/null)
    echo "[$TIMESTAMP] [EDIT] $FILE" >> "$LOG_DIR/events.log" 2>/dev/null
    ;;
  Write)
    FILE=$(basename "$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)" 2>/dev/null)
    echo "[$TIMESTAMP] [WRITE] $FILE" >> "$LOG_DIR/events.log" 2>/dev/null
    ;;
esac

echo '{"decision": "allow"}'
