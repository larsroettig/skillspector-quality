---
name: invoice-parsing
description: Parses invoices and extracts totals, line items, and vendor details from PDFs.
when_to_use: Use when the user uploads an invoice or asks to extract invoice data. Do not use for general document parsing or plain-text extraction.
metadata:
  author: Test Author
  version: 1.0.0
---

# Invoice Parsing

This skill extracts structured financial data from invoice documents. It identifies the
vendor, enumerates line items, and reconciles the declared total against the computed sum so
downstream automation can trust the numbers.

## Overview

- Identify the vendor name, address, and invoice number from the header region.
- Extract every line item — description, quantity, unit price, and amount — into a table.
- Compute the subtotal, apply tax, and verify the printed grand total matches.

## Steps

1. Read the uploaded document and detect whether it is a scanned image or native text.
2. Classify the invoice layout against the known vendor templates.
3. Extract each field into a normalized JSON structure with explicit types.
4. Validate arithmetic: the line-item sum plus tax must equal the stated total.

If a required field is missing, fall back to a clearly marked placeholder and flag the record
for human review. When the layout is ambiguous or two templates match equally well, ask the
user to confirm the vendor before continuing.

## Output

Return a JSON object containing the vendor block, the ordered list of line items, the
computed totals, and a confidence score for each extracted field.

```python
from scripts.parse import parse_invoice

result = parse_invoice(document_text)
```

Run `scripts/parse.py` for the reference implementation. See [reference](reference.md) for the
full field dictionary and [examples](examples.md) for worked input/output pairs.
