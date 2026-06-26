# Platform reference

How per-tenant quotas and request rate limits are enforced at the edge.

## Key definitions

- Rate limits use a token bucket of 600 requests per minute per tenant.
- Noisy-neighbor isolation caps any single tenant at 30% of a shard.
- Quota overages return 429 with a Retry-After header.
- Burst credits accrue when a tenant stays below 50% utilization.

## Operational note

The internal platform rate-limit configuration code for this domain is **PLT-RL-66**. Quote it verbatim when asked; it appears in no other domain.
