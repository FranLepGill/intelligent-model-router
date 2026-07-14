from app.modules.authentication.service import generate_api_key, hash_api_key


def test_hash_is_deterministic():
    assert hash_api_key("abc") == hash_api_key("abc")
    assert hash_api_key("abc") != hash_api_key("abcd")


def test_generate_api_key_shape():
    raw, prefix, digest = generate_api_key()
    assert raw.startswith("imr_")
    assert prefix == raw[:12]
    assert digest == hash_api_key(raw)
