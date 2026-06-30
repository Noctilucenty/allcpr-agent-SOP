"""Staff-access gating + passcode redaction for the site-operations assistant.

The site may be used by both students and staff, so internal passcodes (room/
gate codes, lockbox codes, Wi-Fi credentials, internal instruction links) must
never be returned in the default/public mode. They are redacted backend-side and
only revealed when a request carries a valid short-lived staff token.

Design notes:
- The staff PIN lives in the ``ALLCPR_STAFF_ACCESS_PIN`` environment variable and
  is read at call time (so tests can set it via monkeypatch). If it is unset, no
  unlock is ever possible and everything stays redacted.
- The unlock endpoint returns an HMAC-signed, expiry-stamped token — never the
  raw PIN. The token is verified by recomputing the signature; nothing about the
  PIN or the codes is ever written to logs.
- An item is treated as a redactable secret iff its ``sensitivity`` is
  ``"internal"`` (or, as a safety net, its ``fact_type`` names a code/password).
  Source-needed / normal items (e.g. the "no listed passcode matches" notice) are
  never redacted.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import List, Tuple

from .schemas import OperationalReference, OperationalReferenceItem

PIN_ENV = "ALLCPR_STAFF_ACCESS_PIN"
SECRET_ENV = "ALLCPR_STAFF_ACCESS_SECRET"
TOKEN_TTL_SECONDS = 8 * 60 * 60  # one working day; effectively session-scoped

# fact_types that always denote a secret value, used as a safety net on top of
# the primary ``sensitivity == "internal"`` rule.
SENSITIVE_FACT_TYPES = {"access_code", "password", "keybox", "door_code", "passcode"}

# Localized copy. Backend is authoritative: the redaction text is written into the
# item value so even raw API consumers (not just the UI) see it.
REDACTION_TEXT = {
    "en": "Restricted internal passcode. Staff must unlock internal access to view it.",
    "zh": "内部密码已隐藏。员工需先解锁内部权限后查看。",
}
UNLOCK_WARNING = {
    "en": "Internal use only. Verify site/building/room before using.",
    "zh": "仅限内部使用。使用前请确认地点/楼栋/房间一致。",
}


def _pin() -> str:
    return (os.environ.get(PIN_ENV) or "").strip()


def staff_access_configured() -> bool:
    """Whether a staff PIN is configured at all (otherwise unlock is impossible)."""
    return bool(_pin())


def _signing_key() -> bytes:
    # Derive the HMAC key from a dedicated secret if present, else from the PIN.
    # Either way the emitted token is an HMAC, never the raw PIN.
    secret = (os.environ.get(SECRET_ENV) or "").strip() or _pin()
    return hashlib.sha256(b"allcpr-staff-access-v1:" + secret.encode("utf-8")).digest()


def verify_pin(pin: object) -> bool:
    """Constant-time compare of a submitted PIN against the configured one."""
    configured = _pin()
    if not configured:
        return False
    submitted = str(pin or "").strip()
    if not submitted:
        return False
    return hmac.compare_digest(submitted, configured)


def issue_token(ttl_seconds: int = TOKEN_TTL_SECONDS) -> str:
    """Return an HMAC-signed, expiry-stamped token (``<expiry>.<hexsig>``)."""
    expiry = int(time.time()) + int(ttl_seconds)
    sig = hmac.new(_signing_key(), str(expiry).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{expiry}.{sig}"


def verify_token(token: object) -> bool:
    """Validate a staff token: well-formed, unexpired, and signature matches."""
    if not _pin():
        return False
    raw = str(token or "").strip()
    if not raw or "." not in raw:
        return False
    expiry_str, sig = raw.split(".", 1)
    try:
        expiry = int(expiry_str)
    except ValueError:
        return False
    if expiry < int(time.time()):
        return False
    expected = hmac.new(_signing_key(), str(expiry).encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


def is_sensitive_item(item: OperationalReferenceItem) -> bool:
    """Whether an operational-reference item carries a redactable secret value.

    Secret values are marked ``sensitivity == "internal"`` in the reviewed source
    (room/gate codes, lockbox codes, Wi-Fi credentials, internal instruction
    links). ``source_needed`` / ``normal`` items — e.g. the "no listed passcode
    matches" notice — are explanatory, never secret, so they are never redacted.
    The ``fact_type`` is used only as a corroborating safety net for items whose
    sensitivity is unset.
    """
    sensitivity = (item.sensitivity or "").strip().casefold()
    if sensitivity == "internal":
        return True
    fact_type = (item.fact_type or "").strip().casefold()
    if not sensitivity and fact_type in SENSITIVE_FACT_TYPES:
        return True
    return False


def redact_references(
    references: List[OperationalReference],
    *,
    unlocked: bool,
    lang: str = "en",
) -> Tuple[List[OperationalReference], bool, bool]:
    """Return ``(refs, sensitive_available, revealed)``.

    When ``unlocked`` is false, every sensitive item's value is replaced with the
    localized redaction message and its sensitivity becomes ``"restricted"`` so the
    UI can render a locked state. When unlocked, values are kept as-is.

    ``sensitive_available`` is whether any sensitive item was present (regardless
    of unlock); ``revealed`` is whether any was actually shown.
    """
    redaction = REDACTION_TEXT.get(lang, REDACTION_TEXT["en"])
    sensitive_available = False
    revealed = False
    out: List[OperationalReference] = []
    for ref in references:
        new_items: List[OperationalReferenceItem] = []
        for item in ref.items:
            if not is_sensitive_item(item):
                new_items.append(item)
                continue
            sensitive_available = True
            if unlocked:
                revealed = True
                new_items.append(item)
            else:
                new_items.append(
                    OperationalReferenceItem(
                        label=item.label,
                        value=redaction,
                        sensitivity="restricted",
                        fact_type=item.fact_type,
                    )
                )
        out.append(
            OperationalReference(
                id=ref.id,
                title=ref.title,
                scenario=ref.scenario,
                source_status=ref.source_status,
                priority=ref.priority,
                items=new_items,
                media_tags=list(ref.media_tags),
                do_not=list(ref.do_not),
            )
        )
    return out, sensitive_available, revealed
