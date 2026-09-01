from __future__ import annotations

from typing import NamedTuple
import hashlib
import json
from typing import Any, Iterable, Mapping

REVISION_KEY = "_fitness_ledger_revision"


class RevisionError(ValueError):
    pass


class RevisionInfo(NamedTuple):
    revision: int
    fingerprint: str
    supersedes_fingerprint: str | None


def canonical_json_bytes(document: Mapping[str, Any]) -> bytes:
    payload = {k: v for k, v in document.items() if k != REVISION_KEY}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_fingerprint(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(document)).hexdigest()


def revision_info(document: Mapping[str, Any]) -> RevisionInfo:
    raw = document.get(REVISION_KEY)
    if raw is None:
        # Legacy/import ledgers predate revision metadata. Treat them as revision zero.
        return RevisionInfo(0, content_fingerprint(document), None)
    if not isinstance(raw, Mapping):
        raise RevisionError(f"{REVISION_KEY} must be an object")
    revision = raw.get("revision")
    fingerprint = raw.get("fingerprint")
    supersedes = raw.get("supersedes_fingerprint")
    if not isinstance(revision, int) or revision < 1:
        raise RevisionError("revision must be a positive integer")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise RevisionError("fingerprint must be a SHA-256 hex string")
    if supersedes is not None and (not isinstance(supersedes, str) or len(supersedes) != 64):
        raise RevisionError("supersedes_fingerprint must be null or a SHA-256 hex string")
    return RevisionInfo(revision, fingerprint, supersedes)


def stamp_next_revision(document: Mapping[str, Any], previous: Mapping[str, Any]) -> dict[str, Any]:
    previous_info = revision_info(previous)
    result = dict(document)
    result.pop(REVISION_KEY, None)
    fingerprint = content_fingerprint(result)
    result[REVISION_KEY] = {
        "revision": previous_info.revision + 1,
        "fingerprint": fingerprint,
        "supersedes_fingerprint": previous_info.fingerprint,
    }
    return result


def select_canonical(documents: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    candidates = list(documents)
    if not candidates:
        raise RevisionError("no ledger candidates")
    infos = [(revision_info(doc), doc) for doc in candidates]
    max_revision = max(info.revision for info, _ in infos)
    newest = [(info, doc) for info, doc in infos if info.revision == max_revision]
    if len(newest) != 1:
        fingerprints = {info.fingerprint for info, _ in newest}
        if len(fingerprints) != 1:
            raise RevisionError(f"conflicting ledger artifacts at revision {max_revision}")
    return newest[0][1]
