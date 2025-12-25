import pytest
from unittest.mock import patch, MagicMock

import JUSU.firebase as fb


def test_init_app_with_missing_dependency():
    # If firebase_admin is absent, our wrapper should raise a clear error
    with patch("JUSU.firebase.firebase_admin", None):
        with pytest.raises(fb.FirebaseError):
            fb.init_app()


def test_verify_id_token_calls_admin_verify(monkeypatch):
    fake_verify = MagicMock(return_value={"sub":"alice"})
    fake_admin = MagicMock()
    fake_admin._apps = [1]
    monkeypatch.setattr("JUSU.firebase.firebase_admin", fake_admin)
    monkeypatch.setattr("JUSU.firebase.fb_auth.verify_id_token", fake_verify)

    payload = fb.verify_id_token("tok")
    assert payload["sub"] == "alice"
    fake_verify.assert_called_once_with("tok")
