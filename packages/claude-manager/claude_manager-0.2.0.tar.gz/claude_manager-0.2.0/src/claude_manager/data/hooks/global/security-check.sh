#!/bin/bash
# Hook PreToolUse: Vérification sécurité avant Edit/Write
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
FILE_NAME=$(basename "$FILE_PATH" 2>/dev/null || echo "unknown")
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // ""' 2>/dev/null)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR" 2>/dev/null

echo "[$TIMESTAMP] [HOOK] security-check | $FILE_NAME" >> "$LOG_DIR/events.log" 2>/dev/null

# Exclure les hooks
if [[ "$FILE_PATH" == *"/.claude/hooks/"* ]]; then
  echo '{"decision": "allow"}'
  exit 0
fi

if echo "$CONTENT" | grep -qE 'ghp_[a-zA-Z0-9]{36}' 2>/dev/null; then
  echo "[$TIMESTAMP] [HOOK] security-check | BLOCKED: $FILE_NAME" >> "$LOG_DIR/events.log" 2>/dev/null
  echo '{"decision": "block", "reason": "Secret detected"}'
  exit 0
fi

echo '{"decision": "allow"}'
