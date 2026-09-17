#!/bin/bash
# notification.sh - Play the attention sound when Claude needs you.
# Notification
#
# Under Auto permission mode the remaining moments that need a human are a
# permission prompt the classifier would not clear, an elicitation dialog
# (AskUserQuestion), and Claude going idle waiting for input. This hook
# plays a sound distinct from the Stop hook's completion chime for those, so
# from another room "finished" and "waiting on you" sound different.
#
# hooks.json matches the notification types that mean "needs input"; this
# script additionally skips anything else defensively, so an unknown type
# never chimes. Silence it with KOKKO_SOUNDS=off, or disable the plugin.
# shellcheck source-path=SCRIPTDIR
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=utils/play-sound.sh
source "$SCRIPT_DIR/utils/play-sound.sh"

input=$(cat)

kind=$(echo "$input" | jq -r '.notification_type // empty' 2>/dev/null)
case "$kind" in
    ""|permission_prompt|idle_prompt|elicitation_dialog)
        play_sound "attention"
        ;;
    *)
        ;;   # auth_success and anything unknown: stay quiet
esac
exit 0
