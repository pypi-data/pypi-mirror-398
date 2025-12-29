from amsdal.cloud.models.base import UpdateDeployStatusResponse as UpdateDeployStatusResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class UpdateDeployAction(CloudActionBase):
    """
    Class to handle the update of deployment status.

    This class provides functionality to update the status of a deployment using the given deployment ID.
    """
    def action(self, deployment_id: str) -> UpdateDeployStatusResponse:
        """
        Updates the status of a deployment with the given deployment ID.

        Args:
            deployment_id (str): The ID of the deployment to be updated.

        Returns:
            UpdateDeployStatusResponse: The response containing the updated deployment status.
        """
