import httpx

from ._base import ApiBeanError


class TransportError(ApiBeanError):
    pass


class ConnectionError(TransportError):
    code = "connection_failed"
    message_template = "Cannot connect to {url}"
    hint = "Check server address or make sure the server is running"


class ReqTimeoutError(TransportError):
    code = "read_timeout"
    message_template = "Request to {url} timed out after {timeout}(s)"
    hint = "Try increasing timeout or check server performance"


def map_httpx_exception(exc: httpx.RequestError, timeout = None, **kwargs) -> TransportError:
    request = exc.request
    url = str(request.url) if request else "<unknown>"

    if isinstance(exc, httpx.ConnectError):
        return ConnectionError(
            message_data={"url": url},
            cause=exc,
        )

    if isinstance(exc, httpx.ReadTimeout):
        return ReqTimeoutError(
            message_data={"url": url, "timeout": timeout or 5.0},
            cause=exc,
        )

    return TransportError(
        message=str(exc),
        cause=exc,
    )
