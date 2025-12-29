from amsdal.cloud.models.base import ListDependenciesDetails as ListDependenciesDetails
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class ListDependenciesAction(CloudActionBase):
    """
    Class to handle the listing of application dependencies.

    This class provides functionality to list dependencies for a given environment and application.
    """
    def action(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> ListDependenciesDetails:
        """
        Executes the action to list application dependencies with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            ListDependenciesDetails: The response containing the list of application dependencies.
        """
