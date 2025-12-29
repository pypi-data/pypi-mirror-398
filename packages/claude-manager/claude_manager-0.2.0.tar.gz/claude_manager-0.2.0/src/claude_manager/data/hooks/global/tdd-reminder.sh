#!/bin/bash
# Hook PostToolUse: Rappel TDD après modification de fichier
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
FILE_NAME=$(basename "$FILE_PATH" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR" 2>/dev/null

echo "[$TIMESTAMP] [HOOK] tdd-reminder | $FILE_NAME" >> "$LOG_DIR/events.log" 2>/dev/null

if [[ "$FILE_PATH" == *".spec."* ]] || [[ "$FILE_PATH" == *".test."* ]]; then
  echo '{"decision": "allow"}'
  exit 0
fi

echo '{"decision": "allow"}'
