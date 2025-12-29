from amsdal.cloud.models.base import GetMonitoringInfoResponse as GetMonitoringInfoResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class GetMonitoringInfoAction(CloudActionBase):
    """
    Class to handle the retrieval of monitoring information.

    This class provides functionality to get monitoring information for a given environment and application.
    """
    def action(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> GetMonitoringInfoResponse:
        """
        Executes the action to retrieve monitoring information with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            GetMonitoringInfoResponse: The response containing the monitoring information.
        """
