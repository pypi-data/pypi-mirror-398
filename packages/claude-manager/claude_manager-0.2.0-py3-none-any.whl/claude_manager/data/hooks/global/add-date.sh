#!/bin/bash
# Hook UserPromptSubmit - Ajoute la date actuelle au contexte
# Le texte envoyé sur stdout devient automatiquement du contexte pour Claude

date_now=$(date "+%Y-%m-%d %H:%M:%S")
day_of_week=$(date "+%A")

echo "<user-prompt-submit-hook>"
echo "Date actuelle: $date_now ($day_of_week)"
echo "</user-prompt-submit-hook>"

exit 0
