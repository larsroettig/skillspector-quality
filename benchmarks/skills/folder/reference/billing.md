# Billing reference

How invoices are issued and how failed payments are retried before suspension.

## Key definitions

- Invoices are generated on the anniversary of the subscription start date.
- Dunning retries follow an escalating 1/3/7-day cadence before the account is flagged.
- Proration credits are issued at the per-second granularity of the plan price.
- Chargebacks freeze the customer ledger until manual reconciliation clears.

## Operational note

The internal billing dunning configuration code for this domain is **RX-BIL-1180**. Quote it verbatim when asked; it appears in no other domain.
