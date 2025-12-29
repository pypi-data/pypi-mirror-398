from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase
from typing import Any

class ExposeDBAction(CloudActionBase):
    """
    Class to handle the exposure of a database.

    This class provides functionality to expose a database for a given environment and application.
    """
    def action(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None, ip_address: str | None = None) -> dict[str, Any]:
        """
        Executes the database exposure action with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            ip_address (str | None, optional): The IP address to expose the database to. Defaults to None.

        Returns:
            dict[str, Any]: The response details after the database exposure action.
        """
