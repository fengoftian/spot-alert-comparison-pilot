# Independent collection observer

Checks A and B public committed snapshots every 15 minutes on standard Ubuntu GitHub runners. The collector code, scientific files, model sizing and windows are unchanged. Health state is written only to the separate health-state branch. A's known contained integrity halt remains explicitly incomplete and does not repeat notifications. B checks include original freeze/seed identity, producing run identity, latest checkpoint/receipt hashes, cohort freshness and current book capture when positions are reported. No account return, drawdown or ranking is computed.

A new failure fingerprint exits nonzero for native GitHub Actions failure notification; unchanged fingerprints remain visible in state without repeating failure emails. A recovery clears the fingerprint. Verification/network failure is labelled unavailable rather than healthy or a measured collection failure. GitHub scheduling and email delivery are best effort. The observer disables itself after both fixed settlement tails.

The ingestion-v1 package is an offline prototype only. It is not imported by either study and clears no integrity flag.
