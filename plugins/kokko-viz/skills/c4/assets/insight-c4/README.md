# insight-c4

The renderer behind every diagram in a `codemap/`. It reads a schema 2
`<level>.c4.json` spec and writes an Insight-branded HTML page, a standalone
SVG and a PNG, refusing any spec that breaks a C4 labelling rule. The linter
re-checks what was drawn.

```bash
python3 render.py 'codemap/**/*.c4.json' --png
python3 render.py 'codemap/**/*.c4.json' --check    # C4, spec and geometry checks only
python3 lint.py 'codemap/**/*.svg'                  # C4 lint rules on the output, by rule id
python3 render.py 'examples/*.c4.json' --check      # self-test on the bundled examples
```

| File | Role |
| ---- | ---- |
| `render.py` | CLI, SVG emission with C4 markup, title, generated key, icon inlining, page shell, geometry checks |
| `rules.py` | the C4 model, spec validation and the C4 lint rules, shared by both CLIs |
| `lint.py` | rebuilds the model from a rendered SVG and runs the rules, plus the key-coverage checks. A figure whose root carries `data-c4-diagram="none"` (a supplementary view that is not a C4 diagram, such as a module view of a shared library) is reported as skipped, never as passed. N7 reads a container's name for library words, and its technology only when the technology names the element itself as a library, JAR, DLL or bus: an SDK or package it uses does not make it a library |
| `layout.py` | band layout, nested boundaries and the orthogonal router |
| `tokens.py` | Insight design tokens: colour roles, treatments, type ramp, geometry |
| `examples/` | a valid context, container and component spec for one system, to copy from |

Pure standard library; only `--png` shells out, to Playwright, `rsvg-convert`
or `magick`. Official Microsoft Azure and Fabric icons are found in the
`insight-diagram-design` skill, or passed with `--icons DIR`.

The C4 semantics, the spec schema, the lint rules and the budget are in
`../../references/insight-diagrams.md`.

**Upstream is the `kokko-viz` plugin.** A copy vendored into a repo's
`codemap/.insight-c4/` is a build tool: fix the plugin, then re-copy.
