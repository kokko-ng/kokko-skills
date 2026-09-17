# kokko-viz

C4 architecture visualization: generate, update, and verify C4 model
diagrams from a codebase. The three skills run forked and delegate to two
plugin agents: `c4-mapper` (analysis and edits, with the `c4` authoring
rules preloaded) and `c4-checker` (read-only mechanical re-checks on a
small model). Shared templates live in
`skills/c4/references/c4-templates.md`.

```bash
/plugin install kokko-viz@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/c4-map [target-directory]` ‡ | Generate a hierarchical C4 architecture map (context/containers/components) from a codebase |
| `/c4-update [system-id]` ‡ | Update an existing C4 model to match current code changes |
| `/c4-verify [system-id]` ‡ | Verify C4 diagrams against the codebase and auto-fix discrepancies |
| `/c4` | Authoring rules and shared templates for C4 architecture and codemap documents - mandatory source-file hyperlinks, no validation report files, template and diagram conventions |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Agents

| Agent | Role |
| ----- | ---- |
| `kokko-viz:c4-mapper` | Maps or edits one C4 level; the `c4` skill is preloaded, so it reads the templates itself |
| `kokko-viz:c4-checker` | Verifies folders, includes, links, and image pairing; read-only, small model |
