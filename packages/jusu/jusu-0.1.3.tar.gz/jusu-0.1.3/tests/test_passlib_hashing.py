from JUSU.auth import hash_password, verify_password


def test_hash_and_verify_with_passlib():
    salt, hashed = hash_password("secret")
    # When passlib is installed we expect salt to be an empty string
    assert isinstance(hashed, str)
    # verify should succeed
    assert verify_password("secret", salt, hashed)


def test_legacy_hashing_compat():
    # Simulate legacy by providing a non-empty salt and using the legacy hash
    salt, legacy_hash = hash_password("secret", salt="somesalt")
    assert salt == "somesalt"
    assert verify_password("secret", salt, legacy_hash)
