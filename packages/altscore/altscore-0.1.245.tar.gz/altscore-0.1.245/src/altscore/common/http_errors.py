from json import loads
from functools import wraps
from httpx import HTTPStatusError
from loguru import logger


def retry_on_401(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.info("Token expired, renewing and retrying")
                args[0].renew_token()  # Assuming the first argument is self
                logger.info("Token renewed, retrying")
                return f(*args, **kwargs)
            else:
                raise

    return wrapper


def retry_on_401_async(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.info("Token expired, renewing and retrying")
                args[0].renew_token()  # Assuming the first argument is self
                logger.info("Token renewed, retrying")
                return await f(*args, **kwargs)
            else:
                raise

    return wrapper


def raise_for_status_improved(httpx_request) -> None:
    request = httpx_request._request
    if request is None:
        raise RuntimeError(
            "something went wrong, please report this issue"
        )

    if httpx_request.is_success:
        return

    # Try to parse JSON response for more details
    try:
        parsed_text = loads(httpx_request.text)
    except:
        parsed_text = httpx_request.text[:200]  # First 200 characters if not JSON

    message = (
        "{error_type} '{0.status_code} {0.reason_phrase}' for url '{0.url}'\n"
    )

    status_class = httpx_request.status_code // 100
    error_types = {
        1: "Informational response",
        3: "Redirect response",
        4: "Client error",
        5: "Server error",
    }
    error_type = error_types.get(status_class, "Invalid status code")
    message = message.format(httpx_request, error_type=error_type) + "Response: " + str(parsed_text) + "\n"
    raise HTTPStatusError(message, request=request, response=httpx_request)
