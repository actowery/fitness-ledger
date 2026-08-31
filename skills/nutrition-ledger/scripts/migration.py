"""Idempotent, non-destructive ledger schema migration helpers."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

from product_identity import formulation_fingerprint


def _stable_id(food: str) -> str:
    return "fm-" + hashlib.sha256(food.strip().casefold().encode()).hexdigest()[:16]


def migrate_ledger_v2(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Upgrade legacy records while preserving values, IDs, revisions, and tombstones."""
    migrated = copy.deepcopy(dict(ledger))
    migrated.setdefault("food_master", [])
    for entry in migrated.get("entries", []):
        if not entry.get("food_master_id"):
            entry["food_master_id"] = _stable_id(str(entry.get("food_product") or "unknown"))
        entry.setdefault("revision", 1)
        entry.setdefault("deleted_at", None)
    migrated["schema_version"] = "2.0.0"
    return migrated


def enrich_food_masters(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Fill identity/version metadata derivable from existing master data only."""
    migrated = copy.deepcopy(dict(ledger))
    entries_by_master: dict[str, list[Mapping[str, Any]]] = {}
    for entry in migrated.get("entries", []):
        entries_by_master.setdefault(entry.get("food_master_id"), []).append(entry)
    for master in migrated.setdefault("food_master", []):
        master.setdefault("gtin", master.get("upc_barcode"))
        master.setdefault("upc", master.get("upc_barcode"))
        master.setdefault("product_name", master.get("food_name"))
        master.setdefault("brand_owner", master.get("brand"))
        master.setdefault("manufacturer", None)
        master.setdefault("package_size", None)
        master.setdefault("source_product_id", master.get("source_url_or_id"))
        master.setdefault("source_url", master.get("source_url_or_id"))
        master.setdefault("label_effective_date", master.get("date_last_verified"))
        master.setdefault("first_seen_at", min((e.get("created_at") for e in entries_by_master.get(master.get("food_master_id"), []) if e.get("created_at")), default=None))
        verified = master.get("date_last_verified")
        master.setdefault("last_verified_at", f"{verified}T00:00:00+00:00" if verified else None)
        master.setdefault("verification_source", master.get("source_type"))
        master.setdefault("formulation_hash", formulation_fingerprint({**master, **(master.get("nutrients") or {})}))
        master.setdefault("food_master_version", 1)
        master.setdefault("supersedes_food_master_id", None)
        master.setdefault("status", "active" if master.get("active", True) else "inactive")
    migrated["schema_version"] = "2.1.0"
    return migrated
