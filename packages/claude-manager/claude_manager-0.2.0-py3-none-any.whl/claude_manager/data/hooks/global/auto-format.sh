#!/bin/bash
# Hook PostToolUse: Auto-format fichiers frontend après modification
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
FILE_NAME=$(basename "$FILE_PATH" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR" 2>/dev/null

echo "[$TIMESTAMP] [HOOK] auto-format | $FILE_NAME" >> "$LOG_DIR/events.log" 2>/dev/null

if [[ -n "$FILE_PATH" && "$FILE_PATH" == *"/frontend/"* ]]; then
  case "$FILE_PATH" in
    *.vue|*.ts|*.js|*.css)
      cd "$(dirname "$FILE_PATH")" 2>/dev/null
      npx prettier --write "$FILE_PATH" >/dev/null 2>&1 || true
      ;;
  esac
fi

echo '{"decision": "allow"}'
