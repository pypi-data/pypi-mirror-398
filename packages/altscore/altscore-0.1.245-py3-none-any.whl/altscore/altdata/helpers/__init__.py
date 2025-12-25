def build_headers(module):
    if isinstance(module.altscore_client.api_key, str):
        return {"API-KEY": module.altscore_client.api_key}
    elif isinstance(module.altscore_client.user_token, str):
        user_token = module.altscore_client.user_token.replace("Bearer ", "")
        return {"Authorization": f"Bearer {user_token}"}
    return {}
