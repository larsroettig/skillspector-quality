# Link hygiene is scored, not silently ignored

`dim_structural_coherence` gains a `link_valid` sub-signal that penalizes three previously
unscored link defects: **broken links**, **platform-coupled links** (including
case-mismatches), and **redundant links**. Before this, `_link_graph` dropped any unresolved
link target without trace, so a link to a missing file, an absolute `/Users/...` path, or a
duplicated link all cost **zero** points.

## Scoring

Inside Structural Coherence (weight 13), the sub-weights become:

```
headings   0.40   reachable 0.25   acyclic 0.10   link_valid 0.25
link_valid = clamp01(1 - (0.34·broken + 0.34·platform + 0.10·redundant))
```

`broken` includes case-mismatches. Broken and platform-coupled links are real failures and
sting (≈3 zero the sub-signal); redundant links are minor token waste and only shave.

## Decisions and trade-offs

- **Text-targets-only broken detection.** The loader (`skillspector.nodes.resolve_input`) reads
  only text suffixes into `file_cache`; binary assets (`.pptx/.png/.pdf`) are absent. So a link
  to a real `template.pptx` is indistinguishable from a link to a missing file. We therefore
  flag a link broken only when its target has a text suffix AND is unresolved — never binary
  assets. *Rejected:* "verify all files" (extend the loader to record binary names) — larger
  change to the shared scanner contract; and "flag any unresolved link" — would false-positive
  every valid asset link.
- **Case-mismatch as a distinct sub-type.** A target that resolves only case-insensitively is
  the classic "works on my Mac, breaks in Linux CI" bug. Scored at broken severity with a
  specific message rather than folded into the generic broken bucket.
- **Redundancy = markdown links only.** Skills legitimately tell the agent to read a reference
  file at several workflow steps via bare/backtick paths; counting those as redundant would
  punish good per-step guidance (measured: one real skill had 12 such repeats). Only literal
  `[text](target)` duplicates count. Broken + platform checks still apply to both markdown
  links and bare `reference/...` paths.
- **Severity weights.** Broken/platform 0.34, redundant 0.10 — chosen so a single broken link
  is a noticeable but not catastrophic dent, and ~3 zero the sub-signal.

## Limitation

`SCRIPT_PATH_RE` only matches `scripts|assets|references|reference/...` paths, so a bare
absolute path typed in prose (not inside a `[](...)`) is not extracted. Platform-coupled
detection is therefore markdown-link-scoped in practice. A prose-wide absolute-path regex is a
possible later enhancement but risks flagging documentation examples.

## Consequences

- Broken/platform/redundant links now lower the score and are named in the dimension label.
- Each is independently configurable (`link.broken`, `link.platform`, `link.case-mismatch`,
  `link.redundant`) and gateable via strict mode (see ADR-0006).
- Found a real defect on first run: a skill linking a non-existent `CHANGELOG.md`.
