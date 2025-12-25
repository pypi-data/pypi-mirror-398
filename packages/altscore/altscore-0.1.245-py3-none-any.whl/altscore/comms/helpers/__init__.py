from typing import Optional


def build_headers(module, **kwargs):
    headers = {}
    if isinstance(module.altscore_client.user_token, str):
        user_token = module.altscore_client.user_token.replace("Bearer ", "")
        headers["Authorization"] = f"Bearer {user_token}"
    return headers
