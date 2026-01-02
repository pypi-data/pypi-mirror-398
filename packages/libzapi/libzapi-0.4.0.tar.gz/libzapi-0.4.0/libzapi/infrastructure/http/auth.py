from base64 import b64encode


def oauth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def api_token_headers(email: str, api_token: str) -> dict[str, str]:
    basic = b64encode(f"{email}/token:{api_token}".encode()).decode()
    return {"Authorization": f"Basic {basic}"}
