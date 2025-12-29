from amsdal.cloud.models.base import ListEnvsResponse as ListEnvsResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class ListEnvsAction(CloudActionBase):
    """
    Class to handle the listing of environments.

    This class provides functionality to list environments for a given application.
    """
    def action(self, *, application_name: str | None = None, application_uuid: str | None = None) -> ListEnvsResponse:
        """
        Executes the action to list environments with the given parameters.

        Args:
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            ListEnvsResponse: The response containing the list of environments.
        """
