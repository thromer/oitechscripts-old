import abc
from _typeshed import Incomplete

class _BaseCredentials(metaclass=abc.ABCMeta):
    token: Incomplete
    def __init__(self) -> None: ...
    @abc.abstractmethod
    def refresh(self, request): ...
