from amsdal.cloud.models.base import CreateSessionDetails as CreateSessionDetails
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class CreateSessionAction(CloudActionBase):
    """
    Class to handle the creation of a client session.
    """
    def action(self, encrypted_data: bytes) -> CreateSessionDetails:
        """
        Executes the client session creation action with the given encrypted data.

        Args:
            encrypted_data (bytes): The encrypted data required for session creation.

        Returns:
            CreateSessionDetails: The response model containing the details of the created session.
        """
