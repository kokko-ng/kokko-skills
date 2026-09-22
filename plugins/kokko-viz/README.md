# kokko-viz

C4 architecture visualization: generate, update, and verify C4 model
diagrams from a codebase, drawn in the **Insight Enterprises design
system**. The three skills run forked and delegate to two plugin agents:
`c4-mapper` (analysis and edits, with the `c4` authoring rules preloaded)
and `c4-checker` (read-only mechanical re-checks on a small model).

## Diagrams

Each level is a JSON spec you author (`context.c4.json`) rendered to an
Insight-branded page, SVG and PNG by `skills/c4/assets/insight-c4/render.py`
— a pure standard-library generator that owns the palette, the type ramp,
the official Azure and Fabric icons, the six connector rules and the 4px
grid, so a diagram that renders clean is on brand by construction. Edit the
spec, never the output.

```bash
python3 skills/c4/assets/insight-c4/render.py 'codemap/**/*.c4.json' --png
```

PlantUML was the previous backend and is gone. `/c4-verify` converts a
`.puml` codemap to specs and deletes the leftovers.

Shared references live in `skills/c4/references/`:
`insight-diagrams.md` (visual grammar, spec schema, budget) and
`c4-templates.md` (folders, markdown, phase JSON).

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
| `/c4` | Authoring rules and shared templates for C4 architecture and codemap documents - Insight-branded diagrams rendered from JSON specs, mandatory source-file hyperlinks, no validation report files, template and diagram conventions |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Agents

| Agent | Role |
| ----- | ---- |
| `kokko-viz:c4-mapper` | Maps or edits one C4 level; the `c4` skill is preloaded, so it reads the templates itself |
| `kokko-viz:c4-checker` | Verifies folders, includes, links, and image pairing; read-only, small model |
