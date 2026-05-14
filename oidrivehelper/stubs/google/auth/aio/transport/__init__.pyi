import abc
from _typeshed import Incomplete
from typing import AsyncGenerator, Mapping

DEFAULT_RETRYABLE_STATUS_CODES: Incomplete
DEFAULT_MAX_RETRY_ATTEMPTS: int

class Response(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def status_code(self) -> int: ...
    @property
    @abc.abstractmethod
    def headers(self) -> Mapping[str, str]: ...
    @abc.abstractmethod
    async def content(self, chunk_size: int) -> AsyncGenerator[bytes, None]: ...
    @abc.abstractmethod
    async def read(self) -> bytes: ...
    @abc.abstractmethod
    async def close(self): ...

class Request(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def __call__(self, url: str, method: str, body: bytes | None, headers: Mapping[str, str] | None, timeout: float, **kwargs) -> Response: ...
    async def close(self) -> None: ...
