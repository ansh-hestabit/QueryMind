"""
Simple PII masking utility for Day 4 MVP.
"""
from __future__ import annotations

import re


PII_KEYWORDS = ("email", "phone", "ssn", "social_security", "mobile")


def _mask_value(value: str) -> str:
    if "@" in value:
        parts = value.split("@", 1)
        name = parts[0]
        masked_name = (name[:2] + "***") if len(name) > 2 else "***"
        return masked_name + "@" + parts[1]
    digits = re.sub(r"\D", "", value)
    if len(digits) >= 9:
        return "***-**-" + digits[-4:]
    if len(digits) >= 7:
        return "***-***-" + digits[-4:]
    return "***"


def mask_pii_rows(rows: list[dict]) -> list[dict]:
    masked = []
    for row in rows:
        out = {}
        for key, val in row.items():
            key_l = key.lower()
            if any(k in key_l for k in PII_KEYWORDS) and val is not None:
                out[key] = _mask_value(str(val))
            else:
                out[key] = val
        masked.append(out)
    return masked
