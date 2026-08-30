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

## Scheduled combined synchronization

The nutrition ledger's initialization contract owns the daily schedule in `sync.daily_sync_time_local`, defaulting to `23:55` local time. The scheduler must use the persisted IANA timezone and invoke `run_combined_sync` at that local wall-clock time. Every run pulls nutrition, Caliber workouts, Apple Health workouts, and Apple Health activity; it must emit a clear success or failure result even when no workouts exist. This is an orchestration contract for the host application: installing this skills-only plugin does not itself create an operating-system or ChatGPT automation.

Use the helpers with fixtures first. Add live connectors only outside this skills-only package, with separate authentication and privacy review.

## Safety boundary

Do not infer health conditions or prescribe medical treatment from workout/activity data. Keep source provenance and uncertainty visible whenever data is incomplete or conflicting.
