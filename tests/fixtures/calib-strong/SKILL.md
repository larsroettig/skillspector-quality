---
name: calib-strong
description: Reconcile supplier invoices against purchase orders and flag variances. Use when a finance analyst uploads a PDF invoice batch, when quarterly accruals need vendor-level validation, or when a three-way match fails. Do not use for expense reports, payroll runs, or credit-note issuance — those follow separate approval chains.
---

# Invoice Reconciliation

Match each supplier invoice against its originating purchase order and goods-receipt note,
then surface every monetary discrepancy that exceeds the tolerance your controller has
configured. The routine is deterministic: identical inputs always yield identical variance
reports, which matters because auditors replay historical periods.

## Extraction

Parse the invoice header for vendor identifier, document date, currency, and net total.
Line items carry a stock-keeping code, quantity, unit price, and tax jurisdiction. Where a
scanned document yields ambiguous glyphs, prefer the machine-readable XML attachment that
most European suppliers now embed alongside the rendered page.

Normalize currencies to the ledger's reporting denomination using the rate published on the
document date, never the settlement date — retrospective revaluation belongs to treasury,
not accounts payable.

## Matching

A three-way match compares invoice, purchase order, and receipt. Quantity variance beyond
the configured tolerance escalates to the buyer who raised the requisition. Price variance
escalates to category procurement. Timing differences, where goods arrive across a period
boundary, accrue rather than escalate.

Partial deliveries complicate matching: one purchase order can spawn many receipts and many
invoices, so reconciliation operates on cumulative quantities rather than document-to-document
equality.

## Escalation

Route unresolved variances by magnitude and age. Anything above the controller threshold or
older than the escalation window goes to the finance business partner with the supporting
documents attached. See [reference.md](reference.md) for the tolerance matrix and the
jurisdiction-specific tax rules.

## Example

Input:

```json
{
  "invoice": {"vendor": "AC-4471", "net": 12480.00, "currency": "EUR", "lines": 3},
  "purchase_order": {"id": "PO-88213", "net": 12000.00},
  "receipt": {"id": "GR-55190", "quantity_received": 40, "quantity_ordered": 40}
}
```

Output:

```json
{
  "match": "three_way",
  "quantity_variance": 0,
  "price_variance": 480.00,
  "variance_pct": 4.0,
  "action": "escalate_to_category_procurement",
  "reason": "price variance 4.0% exceeds 2.0% tolerance"
}
```

## Usage

Invoke the reconciliation over a directory of invoice documents and a ledger export. The
routine writes one variance report per vendor plus a consolidated summary suitable for the
month-end pack.

Before:

```
invoices/  ledger_export.csv  (no reconciliation performed)
```

After:

```
variance/AC-4471.json  variance/BD-1180.json  variance/_summary.json
```
