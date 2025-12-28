from typing import Awaitable

import aiohttp
import asyncio
import traceback
from typing import Any, Callable, Literal


async def async_fetch_http(
        url: str,
        session: aiohttp.ClientSession,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        proxy: str | None = None,
        headers: dict | None = None,
        data: Any | None = None,
        timeout: float = 15.0,
        rtype: Literal["text", "json", "bytes"] = "text",
        logfctn: Callable[[str], None] | None = None,
) -> tuple[Any, int, int]:
    """
    Generic async fetch function that supports multiple HTTP methods and return types.

    :param url: Target URL.
    :param session: aiohttp.ClientSession instance.
    :param method: HTTP method (default: GET).
    :param proxy: Optional proxy URL.
    :param headers: Optional HTTP headers.
    :param data: Optional payload for POST/PUT requests.
    :param timeout: Request timeout in seconds (default: 15.0).
    :param rtype: Expected return type: 'text', 'json', or 'bytes'.
    :param logfctn: Optional logging function (e.g., print). If None, logging is disabled.
    :return: Tuple (result, status_code, response_size_bytes).
    """
    result: Any = None
    status_code: int = 0
    resp_size: int = 0

    try:
        async with session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data,
                proxy=proxy,
                timeout=timeout,
        ) as resp:
            status_code = resp.status
            content = await resp.read()
            resp_size = len(content)

            if status_code == 200:
                if rtype == "text":
                    result = content.decode("utf-8", errors="ignore")
                elif rtype == "json":
                    try:
                        result = await resp.json(content_type=None)
                    except Exception as e:
                        if logfctn:
                            logfctn(f"[JSONDecodeError] {url}: {e}\n{traceback.format_exc()}")
                elif rtype == "bytes":
                    result = content
                else:
                    raise ValueError(f"Unsupported rtype: {rtype}")

    except asyncio.TimeoutError as e:
        if logfctn:
            logfctn(f"[Timeout] {url}: {e}")
    except aiohttp.ClientError as e:
        if logfctn:
            logfctn(f"[ClientError] {url}: {e}")
    except Exception as e:
        if logfctn:
            logfctn(f"[UnexpectedError] {url}: {e}\n{traceback.format_exc()}")

    return result, status_code, resp_size


async def fwrap(
        fctn: Callable[..., Awaitable[Any]],
        target_url: str,
        proxy: str | None = None,
        headers: dict | None = None,
        timeout: float = 15.0,
        logfctn: Callable[[str], None] | None = None,
        session: aiohttp.ClientSession | None = None,
        **kwargs,  # Accept and pass extra parameters (method, data, rtype, etc.)
) -> Any:
    """
    Generic async wrapper for aiohttp-based request functions.

    Automatically handles session lifecycle:
    - If no session is provided, it creates one safely using `async with`.
    - If a session is provided, it reuses it (no premature closing).

    :param fctn: The async fetch function that takes (url, session, **kwargs).
    :param target_url: The target URL to request.
    :param proxy: Optional proxy URL (per-request basis).
    :param headers: Optional HTTP headers.
    :param timeout: Request timeout in seconds.
    :param logfctn: Optional logging function (e.g., print).
    :param session: Optional existing aiohttp.ClientSession for reuse.
    :param **kwargs: Extra arguments passed through to `fctn` (e.g. method, data, rtype).
    :return: The result returned by `fctn`.
    """
    if session is not None:
        if logfctn:
            logfctn("[fwrap] Using existing session")
        return await fctn(
            target_url,
            session=session,
            proxy=proxy,
            headers=headers or {},
            timeout=timeout,
            logfctn=logfctn,
            **kwargs,
        )

    async with aiohttp.ClientSession() as new_session:
        if logfctn:
            logfctn("[fwrap] Created new session via async with")
        result = await fctn(
            target_url,
            session=new_session,
            proxy=proxy,
            headers=headers or {},
            timeout=timeout,
            logfctn=logfctn,
            **kwargs,
        )
        if logfctn:
            logfctn("[fwrap] Session automatically closed after use")
        return result


def sync_fetch_http(
        url: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        proxy: str | None = None,
        headers: dict | None = None,
        data: Any | None = None,
        timeout: float = 15.0,
        rtype: Literal["text", "json", "bytes"] = "text",
        logfctn: Callable[[str], None] | None = None,
) -> tuple[Any, int, int]:
    """
    Simplest synchronous wrapper around async_fetch_http + fwrap.
    Works in normal Python scripts (not Jupyter or async environments).

    :return: (result, status_code, response_size_bytes)
    """
    return asyncio.run(
        fwrap(
            async_fetch_http,
            target_url=url,
            proxy=proxy,
            headers=headers,
            timeout=timeout,
            logfctn=logfctn,
            method=method,
            data=data,
            rtype=rtype,
        )
    )


if __name__ == '__main__':
    pass
