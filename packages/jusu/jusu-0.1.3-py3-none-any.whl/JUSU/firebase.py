"""Firebase admin helpers for JUSU.

This module provides a minimal, secure-by-default wrapper around the
`firebase_admin` SDK for server-side use.

Security notes (DO NOT commit credentials):
- Use a Service Account JSON file and do **not** check it into source control.
- Prefer setting the `GOOGLE_APPLICATION_CREDENTIALS` env var or using
  GCP metadata (if running on GCP). Do not embed secret JSON strings in
  your code or public repos.
- Verifying ID tokens should be done with the Admin SDK (`auth.verify_id_token`).
"""
from __future__ import annotations

from typing import Optional

try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth, firestore
except Exception:  # pragma: no cover - optional dependency
    firebase_admin = None  # type: ignore


class FirebaseError(Exception):
    pass


def init_app(cred_path: Optional[str] = None, cred_dict: Optional[dict] = None, project_id: Optional[str] = None):
    """Initialize the firebase admin app.

    - `cred_path`: path to a service account JSON file
    - `cred_dict`: a loaded dict of service account JSON (avoid committing this)
    - If neither provided, the SDK will attempt Application Default Credentials.
    """
    if firebase_admin is None:
        raise FirebaseError("`firebase-admin` not installed. Install via `pip install firebase-admin`.")

    # If an app is already initialized, return it
    if firebase_admin._apps:
        return list(firebase_admin._apps.values())[0]

    if cred_dict is not None:
        cred = credentials.Certificate(cred_dict)
    elif cred_path is not None:
        cred = credentials.Certificate(cred_path)
    else:
        # Rely on ADC
        cred = credentials.ApplicationDefault()

    app = firebase_admin.initialize_app(cred, options={"projectId": project_id} if project_id else None)
    return app


def verify_id_token(token: str) -> dict:
    """Verify an ID token (from client SDK) and return the decoded payload.

    Raises FirebaseError on failure. Requires the app to be initialized or ADC to be available.
    """
    if firebase_admin is None:
        raise FirebaseError("`firebase-admin` not installed.")
    try:
        payload = fb_auth.verify_id_token(token)
        return payload
    except Exception as exc:
        raise FirebaseError(f"Failed to verify token: {exc}") from exc


def firestore_client():
    """Return a Firestore client (initializes app if necessary with ADC)."""
    if firebase_admin is None:
        raise FirebaseError("`firebase-admin` not installed.")
    if not firebase_admin._apps:
        init_app()
    return firestore.client()


__all__ = ["init_app", "verify_id_token", "firestore_client", "FirebaseError"]