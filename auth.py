"""One-time interactive login to Tidal via OAuth device flow.

Run this yourself in the terminal:  python auth.py
It prints a link.tidal.com URL — open it in a browser, approve, and the
session token is saved to session.json. No password is handled by this code.
"""
from __future__ import annotations

import tidalapi

from common import save_session


def main() -> None:
    session = tidalapi.Session()
    print("Opening Tidal device login. Visit the link below and approve:\n")
    # Blocks until you approve in the browser (or it times out).
    session.login_oauth_simple()

    if not session.check_login():
        raise SystemExit("Login failed or was not completed in time.")

    save_session(session)
    user = session.user
    name = getattr(user, "first_name", None) or getattr(user, "id", "unknown")
    print(f"\nLogged in successfully (user: {name}). Saved token to session.json.")
    print("Next:  python fetch.py")


if __name__ == "__main__":
    main()
