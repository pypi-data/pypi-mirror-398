from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DestroyDeployAction(CloudActionBase):
    """
    Class to handle the destruction of a deployment.

    This class provides functionality to remove a specified deployment by its ID.
    """
    def action(self, deployment_id: str) -> bool:
        """
        Executes the deployment destruction action with the given parameters.

        Args:
            deployment_id (str): The ID of the deployment to remove.

        Returns:
            bool: True if the deployment destruction action was successful.
        """
