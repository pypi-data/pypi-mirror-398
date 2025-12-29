from abc import ABC
from abc import abstractmethod


class AppConfig(ABC):
    @abstractmethod
    def on_ready(self) -> None: ...
