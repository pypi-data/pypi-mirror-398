import abc
from abc import ABC, abstractmethod

class AppConfig(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def on_ready(self) -> None: ...
