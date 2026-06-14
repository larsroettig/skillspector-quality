# Reference

Field definitions and layout heuristics for invoice parsing.

## Vendor block

- `vendor.name` — the legal entity issuing the invoice, taken from the header.
- `vendor.address` — the billing address printed beneath the name.
- `vendor.tax_id` — the registration or VAT identifier when present.

## Line items

Each line item is an object with a `description`, a numeric `quantity`, a `unit_price`, and a
computed `amount`. The parser preserves the original ordering so totals can be audited row by
row against the source document.

## Totals

The `subtotal` is the sum of line-item amounts. The `tax` is derived from the printed rate,
and the `total` must equal `subtotal + tax`. A mismatch raises a validation warning rather
than silently trusting the printed figure.

## Confidence

Every extracted field carries a confidence score between zero and one. Low-confidence fields
are surfaced for review instead of being dropped, so no information is lost.
