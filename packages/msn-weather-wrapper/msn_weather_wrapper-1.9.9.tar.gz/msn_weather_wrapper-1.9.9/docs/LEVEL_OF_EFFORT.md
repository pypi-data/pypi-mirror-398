# Level of Effort (LOE)

This page documents the observed development timeline and a rough level-of-effort estimate for the MSN Weather Wrapper whitepaper work, based solely on git commit timestamps.

## Summary

- First commit: `711c94a6d7bc3c28827bbb4e5294cd9e058ef074` on 2025-12-02T15:42:52-05:00.
- Last commit: `f7a77a8666d0d0dded6dfd687e4feda764501a0e` on 2025-12-05T18:18:52Z (13:18:52-05:00).
- Wall-clock span: ~69 hours 36 minutes (~2.9 days).
- Estimated active work time (first to last commit per day): ~36 hours.

## Estimated Hours by Day

| Date (local timezone in commits) | First commit | Last commit  | Approx. hours | Notes |
| --- | --- | --- | --- | --- |
| 2025-12-02 | 15:42 | 23:51 | ~8.1 | Project kickoff; initial scaffolding and setup. |
| 2025-12-03 | 12:07 | 20:28 | ~8.4 | Feature and documentation iterations. |
| 2025-12-04 | 09:50 | 23:38 | ~13.8 | Heaviest day (features, docs, fixes). |
| 2025-12-05 | 07:56 | 13:18 | ~5.4 | Final polish, merges, cleanup. |
| **Total** | — | — | **~35.7 (~36)** | Sum of daily first/last windows. |

## Methodology and Assumptions

- Source: git commit author timestamps (`git log --format='%cI'`).
- Hours per day are measured from the first to last commit that day; this captures time between first and last check-in, not continuous effort.
- Actual hands-on time may be lower (breaks between commits) or higher (uncommitted work, reviews, local experiments).
- Timezone shown per commit; some commits use `-05:00`, others UTC. Conversions were normalized when comparing spans.

## Context

- Work focused on the Modern Software Engineering whitepaper (`docs/WHITEPAPER.md` and `artifacts/whitepaper.pdf`).
- The whitepaper outlines architecture, DevEx, testing, security, CI/CD, and recommendations for MSN Weather Wrapper.

## How to Reproduce the Numbers

1. Find the first and latest commit: `git log --reverse --format='%H %cI' | head -n 1` and `git log -1 --format='%H %cI'`.
2. List per-day timestamps: `git log --format='%cI'` and group by date.
3. For each day, compute the span between the first and last commit; sum spans across days.

## Caveats

- LOE based on commit timestamps is a coarse proxy; use it only for high-level sizing.
- Meetings, reviews, and uncommitted work are not reflected.
- Multiple authors or timezones can skew interpretations.
