from amsdal.cloud.models.base import ListDeployResponse as ListDeployResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class ListDeploysAction(CloudActionBase):
    """
    Class to handle the listing of deployments.

    This class provides functionality to list deployments for a given environment.
    """
    def action(self, *, list_all: bool = True) -> ListDeployResponse:
        """
        Executes the action to list deployments with the given parameters.

        Args:
            list_all (bool, optional): Whether to list all deployments. Defaults to True.

        Returns:
            ListDeployResponse: The response containing the list of deployments.
        """
