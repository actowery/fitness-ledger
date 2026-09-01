# Library persistence contract

Fitness Ledger uses ChatGPT Library as its durable persistence boundary. The conversation is the interface; Library artifacts are the record.

## Why persistence is revisioned

Skills provide workflow instructions, but a skills-only plugin does not expose a provider-backed in-place Library mutation action. ChatGPT does, however, persist files that it creates into Library. Therefore the portable ChatGPT/Plus/mobile write primitive is **create a validated successor artifact**, not "replace this exact Library object in place."

Never claim an in-place Library replacement unless the active runtime actually exposes and successfully invokes a guarded Library write/replace action.

## Canonical files

- `Fitness_Ledger_Nutrition_Ledger.json` is the logical canonical nutrition history, food master, provenance, targets, and audit log.
- Existing import names such as `IMPORT_Nutrition_Ledger.json` remain valid logical canonical roots when selected by the user.
- `Fitness_Ledger_Nutrition_Current_State.json` is a rebuildable current-day cache and must never be authoritative by itself.
- `Fitness_Ledger_Nutrition_Weight_Tracker.xlsx` is a reporting projection, not the operational source of truth.

A logical canonical ledger may have multiple Library artifacts over time. Canonical identity is determined by the revision chain below, not by filename uniqueness, creation time alone, or whichever search hit appears first. Existing user-selected logical names are preserved; never duplicate or rename a logical ledger merely because a generic default filename also exists.

## Revision metadata

Newly generated canonical successors carry top-level `_fitness_ledger_revision` metadata:

```json
{
  "_fitness_ledger_revision": {
    "revision": 1,
    "fingerprint": "<sha256 of canonical content excluding this metadata>",
    "supersedes_fingerprint": "<fingerprint of the prior canonical artifact>"
  }
}
```

Legacy/import ledgers without this metadata are revision `0`. The helper in `scripts/library_revision.py` defines the deterministic fingerprinting and selection behavior.

## Read path

1. Search Library for the user's selected logical ledger name and any recognized successor artifacts.
2. Read candidate ledger contents before selecting canon; snippets alone are insufficient; canonical history is the mandatory first read.
3. Select the unique artifact with the highest valid revision using `library_revision.select_canonical` semantics.
4. If two different artifacts claim the same highest revision, stop and report a conflict. Never guess based on timestamp or filename.
5. Only after canonical history has been resolved may the current-state cache be read as a derived cross-check.
6. If cache and canon disagree, canonical history wins; never silently omit a canonical item. A stale cache is a cache-repair event.
7. For date-scoped reports, filter active canonical entries by the configured local date, then reconcile state from that set.

## Mutation path

1. Resolve the current canonical artifact and its fingerprint.
2. Resolve food identity, quantity, nutrient values, provenance, date, and timezone without modifying persisted data.
3. Apply the append, correction, tombstone, target, or food-master mutation in memory.
4. Validate schema, dates, quantities, nutrients, provenance, idempotency, audit history, and cache consistency.
5. Stamp the proposed ledger as the next revision, linking `supersedes_fingerprint` to the exact canonical artifact read in step 1. This supersession fingerprint is the portable equivalent of a current-version guard: if the prior canonical content changed, the successor must be recomputed rather than blindly published.
6. Materialize the complete successor JSON as a newly created ChatGPT file so it is saved to Library. Preserve the user's logical canonical filename when the runtime supports same-name generated files; otherwise use a deterministic revision suffix and retain the logical ledger name in metadata/documentation.
7. Read/search Library again and verify the generated successor's revision and fingerprint. Do not treat a local sandbox file alone as persistence evidence.
8. Rebuild/materialize current state only after canonical successor verification succeeds.
9. If verification fails or a competing revision appeared, report `not persisted` and do not claim success.

No partial mutation is successful.

## Runtime with a real guarded write action

If a future runtime exposes a first-party or approved app action that can atomically replace a retained Library file identity with a current-version guard, that action may be used instead of artifact succession. It must still preserve the same audit, validation, conflict, and read-back guarantees. Capability must be observed in the active runtime; instructions alone are not evidence that it exists.

## Reporting path

Reports use active canonical entries only, fixed meal ordering, explicit unknowns, and the configured IANA timezone. Missing nutrients remain unknown rather than zero. Canonical history wins over cache disagreement; never silently omit a canonical item. A stale cache is a cache-repair event, not permission to under-report canonical history.
