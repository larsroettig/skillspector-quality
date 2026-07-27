# Releasing

How a release is cut, how artifacts are signed, and how anyone can verify them. Written so a
second maintainer could run a release without asking anyone — see
[GOVERNANCE.md](GOVERNANCE.md#continuity-of-access).

## Verifying a release (for consumers)

Every release publishes, per platform, a `.tar.gz`, a `SHA256SUMS` manifest, and a Sigstore
bundle (`.sigstore.json`) for each.

Signing is **keyless**. There is no public key to fetch and no private key held by a maintainer:
cosign exchanges the release workflow's OIDC token for a short-lived certificate binding the
signature to this repository's workflow, and records it in the public Rekor transparency log.
Verification therefore checks *which workflow produced the artifact*, which is a stronger claim
than "someone with the key signed it".

```bash
# 1. Verify the signature on the checksum manifest.
#    The identity flags are the point of the exercise — without them you have only
#    proven that *something* signed it.
cosign verify-blob \
  --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp '^https://github\.com/larsroettig/skillspector-quality/\.github/workflows/release\.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  SHA256SUMS

# 2. Check the tarball digest against the now-trusted manifest.
shasum -a 256 -c SHA256SUMS --ignore-missing
```

A tarball can also be verified directly against its own bundle:

```bash
cosign verify-blob \
  --bundle skillspector-quality-2.0.0-darwin-arm64.tar.gz.sigstore.json \
  --certificate-identity-regexp '^https://github\.com/larsroettig/skillspector-quality/\.github/workflows/release\.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  skillspector-quality-2.0.0-darwin-arm64.tar.gz
```

If verification fails, do not install the artifact — report it via
[SECURITY.md](SECURITY.md).

## Cutting a release (for maintainers)

1. **Write the changelog section first.** Add `## [X.Y.Z] — YYYY-MM-DD` to
   [CHANGELOG.md](CHANGELOG.md) with the changes and a `### Security` heading naming every
   publicly known vulnerability fixed, or stating there were none. The release *will fail*
   without a matching section — this is deliberate, so notes can never silently degrade to a
   commit dump.
2. **Set the version** in `pyproject.toml`. `__version__` is read from package metadata, so
   there is nothing else to update; `tests/test_release_metadata.py` fails if they disagree or
   if the changelog section is missing.
3. **Confirm the version bump matches the change.** A change that makes scores incomparable
   with the previous line is a **major** bump, per
   [GOVERNANCE.md](GOVERNANCE.md#how-decisions-are-made).
4. **Merge to `main`** and let CI go green: tests, coverage ≥ 96%, ruff, mypy, CodeQL, fuzzing.
5. **Create a signed, annotated tag** and push it:

   ```bash
   git tag -s v2.0.0 -m "v2.0.0"
   git push origin v2.0.0
   ```

   `-s` matters. A lightweight tag (`git tag v2.0.0`) is just a pointer with no author, no date,
   and no signature — `git verify-tag` cannot check it. Tags `v1.0.0` and `v1.1.0` predate this
   requirement and are unsigned; they are not retrofitted, because rewriting a published tag
   would break anything already referencing it.

   Signing needs a configured key once:

   ```bash
   git config --global user.signingkey <key-id>   # GPG
   # or, for SSH signing:
   git config --global gpg.format ssh
   git config --global user.signingkey ~/.ssh/id_ed25519.pub
   ```

   Add the public key to GitHub so the tag shows as **Verified**.

6. **The tag triggers the release workflow**, which builds native binaries on three runners,
   smoke-tests each against a fixture, signs the artifacts, and publishes the GitHub release
   with the changelog section as its notes.
7. **Update the Homebrew formula** once the release exists — the formula needs the published
   digests:

   ```bash
   packaging/homebrew/update-formula.sh v2.0.0 ~/src/homebrew-tap/Formula/skillspector-quality.rb
   ```

8. **Verify the published artifacts** using the consumer steps above. Verifying your own release
   is the only way to know the signing step actually worked.

## Dry run

The release workflow accepts `workflow_dispatch` with an existing tag to exercise the build and
signing path without publishing.

## What is not automated

- **Tag signing** happens on the maintainer's machine and needs their key. CI cannot do it —
  that is the point: the tag asserts a human cut this release.
- **The Homebrew formula update** is a separate repository and a manual step.
