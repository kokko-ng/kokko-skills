# kokko-notifications

Sound notifications for Claude Code, so long-running work can be left
alone: a completion chime when Claude finishes a turn, and a distinct
attention sound when Claude is waiting on you (a permission prompt, a
question, or idle waiting for input). From another room, "finished" and
"needs you" sound different.

```bash
/plugin install kokko-notifications@kokko-ng-kokko-cmds
```

## Hooks

| Hook | Event | Purpose |
| ---- | ----- | ------- |
| `stop-notification` | Stop | Plays the completion sound when Claude finishes a turn |
| `notification` | Notification (`permission_prompt`, `idle_prompt`, `elicitation_dialog`) | Plays the attention sound when Claude needs input |

## Environment variables

Sounds go through `hooks/utils/play-sound.sh`. It supports macOS (afplay),
Linux (paplay/aplay), WSL and Git Bash (PowerShell system sounds), and falls
back to a terminal bell in containers.

| Environment Variable | Default | Purpose |
| -------------------- | ------- | ------- |
| `KOKKO_SOUNDS` | `on` | Set to `off` to mute all hook sounds |
| `KOKKO_SOUND_VOLUME` | `1.0` | afplay gain multiplier (macOS); `1.0` = unity |
