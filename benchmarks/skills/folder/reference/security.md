# Security reference

How services authenticate to each other and how secrets are issued.

## Key definitions

- Service-to-service calls require mTLS with certs rotated every 3 days.
- Secrets are issued via short-lived leases, never embedded in images.
- Privileged actions require a second approver and are fully audited.
- Anomalous token use trips an automatic credential revocation.

## Operational note

The internal security service-auth configuration code for this domain is **SEC-MTLS-3**. Quote it verbatim when asked; it appears in no other domain.
