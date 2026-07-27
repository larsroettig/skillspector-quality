---
name: calib-typical
description: Generate release notes from merged pull requests. Use when preparing a tagged release.
---

# Release Notes Generator

Collect merged pull requests since the previous tag and group them into a changelog. The
output follows the conventional-commits categories so downstream tooling can parse it.

## How it works

Read the git history between the previous tag and HEAD. For each merge commit, resolve the
pull request number and fetch its title and labels. Titles that follow the conventional
prefix convention are grouped automatically; anything else lands in a miscellaneous bucket
that a human reviews before publishing.

Labels take precedence over title prefixes when the two disagree, because maintainers
relabel more often than they rewrite commit subjects.

## Categories

Features, fixes, performance work, documentation, and internal chores each get their own
section. Breaking changes are hoisted to the top regardless of their category, with the
migration note extracted from the pull request body.

## Output

The generated file is markdown with one heading per category and one bullet per pull
request, each linking back to the originating discussion. See notes.md for the label
mapping table.

## Example

```bash
generate-release-notes --from v1.4.0 --to HEAD > CHANGELOG-v1.5.0.md
```

The command prints a summary of how many pull requests landed in each category so you can
spot a mis-grouped entry before publishing.
