"""Validation helpers for the food-master catalogue."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any
from urllib.parse import urlparse

NUTRIENT_FIELDS = (
    "calories", "protein_g", "carbohydrates_g", "fat_g", "fiber_g",
    "total_sugars_g", "added_sugars_g", "saturated_fat_g", "trans_fat_g",
    "cholesterol_mg", "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg",
    "magnesium_mg", "phosphorus_mg", "zinc_mg", "copper_mg", "manganese_mg",
    "selenium_mcg", "vitamin_a_mcg_rae", "vitamin_c_mg", "vitamin_d_mcg",
    "vitamin_e_mg", "vitamin_k_mcg", "thiamin_mg", "riboflavin_mg",
    "niacin_mg", "pantothenic_acid_mg", "vitamin_b6_mg", "biotin_mcg",
    "folate_mcg_dfe", "folic_acid_mcg", "vitamin_b12_mcg", "choline_mg",
    "iodine_mcg", "chromium_mcg", "molybdenum_mcg", "monounsaturated_fat_g",
    "polyunsaturated_fat_g", "water_g", "water_oz",
)


def catalogue_issues(masters: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return deterministic, human-readable integrity errors for food masters."""
    issues: list[str] = []
    for master in masters:
        if not isinstance(master, Mapping):
            issues.append("unknown: food-master record must be an object")
            continue
        identity = master.get("food_master_id") or master.get("food_name") or "unknown"
        urls = master.get("source_urls")
        if not isinstance(urls, list) or not urls:
            issues.append(f"{identity}: source_urls must be a non-empty list")
        else:
            for index, url in enumerate(urls):
                parsed = urlparse(url) if isinstance(url, str) else None
                hostname = parsed.hostname if parsed else None
                hostname_parts = hostname.split(".") if hostname else []
                if (parsed is None or parsed.scheme not in {"http", "https"} or
                        not parsed.netloc or len(hostname_parts) < 2 or
                        any(not part for part in hostname_parts) or
                        len(hostname_parts[-1]) < 2 or
                        any(not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part)
                            for part in hostname_parts)):
                    issues.append(f"{identity}: source_urls[{index}] is not a valid HTTP(S) URL")
            if master.get("source_url") != urls[0]:
                issues.append(f"{identity}: source_url must equal source_urls[0]")

        nutrients = master.get("nutrients")
        if not isinstance(nutrients, Mapping):
            issues.append(f"{identity}: nutrients must be an object")
        else:
            for field in NUTRIENT_FIELDS:
                if field not in nutrients:
                    issues.append(f"{identity}: missing nutrient field {field}")

        provenance = master.get("nutrient_provenance")
        if not isinstance(provenance, Mapping):
            issues.append(f"{identity}: nutrient_provenance must be an object")
        else:
            for field in NUTRIENT_FIELDS:
                if field not in provenance:
                    issues.append(f"{identity}: missing provenance field {field}")
    return issues
