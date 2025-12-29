from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DeleteBasicAuthAction(CloudActionBase):
    """
    Class to handle the deletion of basic authentication.

    This class provides functionality to remove basic authentication for a given environment and application.
    """
    def action(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> bool:
        """
        Executes the basic authentication deletion action with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            bool: True if the basic authentication deletion action was successful.
        """
