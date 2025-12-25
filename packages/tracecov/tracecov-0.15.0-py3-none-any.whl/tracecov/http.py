from dataclasses import dataclass


@dataclass
class HttpRequest:
    method: str
    url: str
    body: bytes | None
    headers: dict[str, str]

    __slots__ = ("method", "url", "body", "headers")


@dataclass
class HttpResponse:
    status_code: int
    elapsed: float

    __slots__ = ("status_code", "elapsed")


@dataclass
class HttpInteraction:
    request: HttpRequest
    response: HttpResponse | None
    timestamp: float

    __slots__ = ("request", "response", "timestamp")
