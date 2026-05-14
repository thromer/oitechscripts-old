import abc
from _typeshed import Incomplete

class _BaseAuthorizedSession(metaclass=abc.ABCMeta):
    credentials: Incomplete
    def __init__(self, credentials) -> None: ...
    @abc.abstractmethod
    def request(self, method, url, data=None, headers=None, max_allowed_time=None, timeout=..., **kwargs): ...
    @abc.abstractmethod
    def close(self): ...
