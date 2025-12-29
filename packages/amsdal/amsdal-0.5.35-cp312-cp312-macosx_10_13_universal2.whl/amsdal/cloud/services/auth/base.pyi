import abc
from abc import ABC, abstractmethod

class AuthHandlerBase(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def validate_credentials(self) -> None: ...
