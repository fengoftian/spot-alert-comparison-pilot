# Prospective Binance Spot alert comparison

A fixed, 30-day public-data software/research pilot comparing four price-and-volume alert constructions across 44 Binance Spot crypto pairs. This repository contains the frozen study and its GitHub Actions collector. It does not place orders or access exchange accounts. Capital amounts are simulated account configurations, not fetched balances.

The fixed window is 9 October 2026 10:50 NZDT through 8 November 2026 10:50 NZDT, with a maximum four-hour settlement tail. Rules and dates are pinned in `gen/FREEZE.json`; the four models share execution timing, sizing, fees and risk containment. No short-window CAGR, qualified inference, or best-strategy claim is made.

## Collection

Standard Ubuntu GitHub-hosted runners execute a minute loop within finite leases. State and raw public receipts are checkpointed to the `observations` branch. The scheduler is best effort: delays and missed live books remain explicit. Historical candle recovery does not recover timely books.

No paid runner, Actions artifact/cache storage, Git LFS or paid external API is used. Collection disables its workflow at the fixed tail deadline.

## Verification

The hosted preflight checks migration recovery, the original 23 synthetic engine tests in a disposable copy, frozen identities, and public Binance transport. Passing tests and receipts establish process behavior, not economic edge or trading authority.

The `observations` branch contains the initial state, append-only state journals and raw receipts. `STATUS.json` distinguishes warmup from prospective observations. Final `RESULTS.json`/`RESULTS.md` remain descriptive inputs for a separate review of coverage, simulated execution and whole-account measurement.

## Scope

Spot only; no shorting, leverage, margin, borrowing, exchange credentials or live orders. Returns, when reported, use a continuous whole account including idle cash and show drawdown and deployment. The longer-run research objective remains 10–20% CAGR after trading costs with maximum drawdown no greater than 15%; this 30-day pilot cannot establish that objective.
