from amsdal_utils.lifecycle.producer import LifecycleProducer

from amsdal.contrib.app_config import AppConfig
from amsdal.contrib.frontend_configs.constants import ON_RESPONSE_EVENT
from amsdal.contrib.frontend_configs.lifecycle.consumer import ProcessResponseConsumer


class FrontendConfigAppConfig(AppConfig):
    """
    Application configuration class for frontend configurations.

    This class extends the AppConfig and sets up listeners for lifecycle events
    to process frontend configurations.
    """

    def on_ready(self) -> None:
        """
        Registers a listener for the ON_RESPONSE_EVENT to process responses
        using the ProcessResponseConsumer.

        Returns:
            None
        """
        LifecycleProducer.add_listener(ON_RESPONSE_EVENT, ProcessResponseConsumer)  # type: ignore[arg-type]
