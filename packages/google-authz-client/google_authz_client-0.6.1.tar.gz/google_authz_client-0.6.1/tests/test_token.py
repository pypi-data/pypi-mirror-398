from google_authz_client.token import discover_token, extract_bearer_token


def test_extract_bearer_token_handles_prefix():
    assert extract_bearer_token("Bearer foo") == "foo"
    assert extract_bearer_token("bearer bar") == "bar"
    assert extract_bearer_token("token") == "token"
    assert extract_bearer_token(None) is None


def test_discover_token_prefers_cookie():
    headers = {"Authorization": "Bearer ignored"}
    cookies = {"session": "cookie-token"}
    assert discover_token(headers, cookies) == "cookie-token"


def test_discover_token_falls_back_to_header():
    headers = {"Authorization": "Bearer header-token"}
    cookies = {}
    assert discover_token(headers, cookies) == "header-token"
