# Examples

## Example: simple invoice

Input:

```text
Vendor: Acme Corp
Total: $100.00
```

Output:

```json
{"vendor": "Acme Corp", "total": 100.0}
```

## Example: missing total

Input:

```text
Vendor: Globex
```

Output:

```json
{"vendor": "Globex", "total": null, "flag": "missing total"}
```
