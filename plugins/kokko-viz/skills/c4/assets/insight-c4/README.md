# insight-c4

The renderer behind every diagram in a `codemap/`. It reads a `<level>.c4.json`
spec and writes an Insight-branded HTML page, a standalone SVG and a PNG.

```bash
python3 render.py 'codemap/**/*.c4.json' --png
python3 render.py 'codemap/**/*.c4.json' --check    # geometry checks only
```

| File | Role |
| ---- | ---- |
| `render.py` | CLI, SVG emission, icon inlining, page shell, checks |
| `layout.py` | band layout and the orthogonal router |
| `tokens.py` | Insight design tokens: colour roles, treatments, type ramp, geometry |

Pure standard library; only `--png` shells out, to Playwright, `rsvg-convert`
or `magick`. Official Microsoft Azure and Fabric icons are found in the
`insight-diagram-design` skill, or passed with `--icons DIR`.

The spec schema, the C4-element-to-treatment table and the budget are in
`../../references/insight-diagrams.md`.

**Upstream is the `kokko-viz` plugin.** A copy vendored into a repo's
`codemap/.insight-c4/` is a build tool: fix the plugin, then re-copy.
