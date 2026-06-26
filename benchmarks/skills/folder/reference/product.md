# Product reference

How product usage events are captured, partitioned, and aggregated.

## Key definitions

- The api_usage table partitions on the event_hour column for query pruning.
- Events are deduplicated on (account_id, event_id) within a 24h window.
- Feature adoption is the ratio of weekly active to entitled accounts.
- Schema changes are gated behind a backward-compatible contract test.

## Operational note

The internal product analytics-event configuration code for this domain is **PRD-EVTH-9**. Quote it verbatim when asked; it appears in no other domain.
