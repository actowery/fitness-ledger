---
name: fitness-sync
description: Reconcile workout and activity-source snapshots into deterministic, provenance-preserving fitness facts; use for validation, rest-day checks, and source conflicts.
---

# Fitness Sync

Use this skill to normalize and reconcile workout and activity snapshots that the user provides or has already connected. It is source-agnostic: connectors belong outside this plugin.

## Core rules

- Preserve raw source observations; do not fabricate a source value or treat absence as deletion.
- Require stable workout IDs, valid dates, non-negative measurements, and unique set identities.
- A complete zero-result workout pull is valid and must not delete prior canonical workouts.
- Reconcile by stable workout ID; classify records as new, updated, or unchanged.
- Do not add overlapping activity totals from different sources.
- Manual overrides outrank automated sources. Configure automated precedence explicitly for each deployment and retain conflicts as diagnostics.
- Reject incomplete, truncated, or future-dated activity responses before publishing a derived daily fact.

## Deterministic helpers

`scripts/fitness_sync.py` validates and reconciles source snapshots without network access. `scripts/combined_sync.py` demonstrates dependency-injected orchestration; it always runs the configured source checks, including on rest days.

Use the helpers with fixtures first. Add live connectors only outside this skills-only package, with separate authentication and privacy review.

## Safety boundary

Do not infer health conditions or prescribe medical treatment from workout/activity data. Keep source provenance and uncertainty visible whenever data is incomplete or conflicting.
