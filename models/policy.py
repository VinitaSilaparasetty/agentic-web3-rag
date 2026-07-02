# SPDX-FileCopyrightText: you
# SPDX-License-Identifier: MIT
from __future__ import annotations

ALLOWED_LICENSES = {
    "MIT","APACHE-2.0","BSD-2-CLAUSE","BSD-3-CLAUSE",
    "MPL-2.0","CC-BY-4.0","CC0-1.0","UNLICENSE",
}

def normalize(lic: str | None) -> str | None:
    return lic.strip().upper() if lic else None

def license_ok(lic: str | None) -> bool:
    lic = normalize(lic)
    return bool(lic and lic in ALLOWED_LICENSES)
