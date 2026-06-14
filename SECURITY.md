# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest release on `main` | Yes |
| Older releases | No — please upgrade |

## Scope

skillspector-quality is a **static analysis tool**: it reads skill files from disk and
produces a numeric score. It makes no network calls in the deterministic scoring path and
never modifies the files it scans.

The optional LLM advisory path (`commentary.py`) calls an external API using a key you
supply. Vulnerabilities in that path (e.g. prompt injection via a crafted skill file) are
in scope.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues privately to:

```
security@lroettig.dev
```

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal skill file or command is ideal)
- Any suggested remediation, if you have one

We aim to acknowledge reports within **48 hours** and to issue a fix or workaround
within **14 days** for confirmed issues.

## Disclosure policy

We follow coordinated disclosure: we ask that you give us at least 14 days before
publishing details publicly, so users have time to upgrade.

## OpenSSF recognition

This project aspires to meet the [OpenSSF Best Practices Badge](https://bestpractices.coreinfrastructure.org/)
criteria. If you find a gap between our practices and the criteria, please open an issue.
