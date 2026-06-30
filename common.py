"""Shared helpers: paths and Tidal session load/save."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Windows consoles default to cp1252 and choke on Unicode (→, •, accents).
# Force UTF-8 on stdout/stderr so reports print cleanly everywhere.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SESSION_FILE = ROOT / "session.json"
PLAYLISTS_FILE = DATA / "playlists.json"
GENRES_FILE = DATA / "genres.json"
REPORT_FILE = DATA / "report.md"
CLASSIFICATION_FILE = DATA / "classification.json"
UNCLASSIFIED_FILE = DATA / "unclassified.json"

DATA.mkdir(exist_ok=True)


def save_session(session) -> None:
    """Persist OAuth tokens so future runs don't need to re-login."""
    expiry = session.expiry_time
    SESSION_FILE.write_text(
        json.dumps(
            {
                "token_type": session.token_type,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expiry_time": expiry.isoformat() if isinstance(expiry, datetime) else None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_session():
    """Return a logged-in tidalapi.Session from session.json, or raise if missing/invalid."""
    import tidalapi

    if not SESSION_FILE.exists():
        raise SystemExit("No session.json found. Run:  python auth.py  first.")

    data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    expiry = data.get("expiry_time")
    expiry_dt = datetime.fromisoformat(expiry) if expiry else None

    session = tidalapi.Session()
    ok = session.load_oauth_session(
        data["token_type"],
        data["access_token"],
        data.get("refresh_token"),
        expiry_dt,
    )
    if not ok or not session.check_login():
        raise SystemExit("Saved session is invalid/expired. Re-run:  python auth.py")

    # Tokens may have been refreshed during load — persist the latest.
    save_session(session)
    return session
