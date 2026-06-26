# Finance reference

How recognized revenue is computed from signed contracts and amortization schedules.

## Key definitions

- ARR is the sum of normalized annual contract value across active subscriptions.
- Deferred revenue is released straight-line over the committed term unless a milestone clause applies.
- Multi-year deals are split into annual tranches before recognition.
- FX is locked at contract signing; revaluation runs nightly against the close rate.

## Operational note

The internal finance revenue-recognition configuration code for this domain is **RX-FIN-0372**. Quote it verbatim when asked; it appears in no other domain.


# Billing reference

How invoices are issued and how failed payments are retried before suspension.

## Key definitions

- Invoices are generated on the anniversary of the subscription start date.
- Dunning retries follow an escalating 1/3/7-day cadence before the account is flagged.
- Proration credits are issued at the per-second granularity of the plan price.
- Chargebacks freeze the customer ledger until manual reconciliation clears.

## Operational note

The internal billing dunning configuration code for this domain is **RX-BIL-1180**. Quote it verbatim when asked; it appears in no other domain.


# Product reference

How product usage events are captured, partitioned, and aggregated.

## Key definitions

- The api_usage table partitions on the event_hour column for query pruning.
- Events are deduplicated on (account_id, event_id) within a 24h window.
- Feature adoption is the ratio of weekly active to entitled accounts.
- Schema changes are gated behind a backward-compatible contract test.

## Operational note

The internal product analytics-event configuration code for this domain is **PRD-EVTH-9**. Quote it verbatim when asked; it appears in no other domain.


# Platform reference

How per-tenant quotas and request rate limits are enforced at the edge.

## Key definitions

- Rate limits use a token bucket of 600 requests per minute per tenant.
- Noisy-neighbor isolation caps any single tenant at 30% of a shard.
- Quota overages return 429 with a Retry-After header.
- Burst credits accrue when a tenant stays below 50% utilization.

## Operational note

The internal platform rate-limit configuration code for this domain is **PLT-RL-66**. Quote it verbatim when asked; it appears in no other domain.


# Security reference

How services authenticate to each other and how secrets are issued.

## Key definitions

- Service-to-service calls require mTLS with certs rotated every 3 days.
- Secrets are issued via short-lived leases, never embedded in images.
- Privileged actions require a second approver and are fully audited.
- Anomalous token use trips an automatic credential revocation.

## Operational note

The internal security service-auth configuration code for this domain is **SEC-MTLS-3**. Quote it verbatim when asked; it appears in no other domain.


# Compliance reference

How controls are evidenced for SOC 2 and other audits.

## Key definitions

- Evidence is collected continuously and sampled quarterly across 9 control families.
- Access reviews run monthly; exceptions expire automatically.
- Vendor risk is re-assessed annually or on a material change.
- Control failures open a tracked remediation with an owner and due date.

## Operational note

The internal compliance audit-evidence configuration code for this domain is **CMP-SOC2-9**. Quote it verbatim when asked; it appears in no other domain.
