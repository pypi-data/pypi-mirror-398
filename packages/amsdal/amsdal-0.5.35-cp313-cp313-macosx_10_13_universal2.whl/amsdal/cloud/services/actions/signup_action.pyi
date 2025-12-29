from amsdal.cloud.models.base import SignupReponseCredentials as SignupReponseCredentials
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class FreeSignupAction(CloudActionBase):
    """
    Class to handle the free signup action.

    This class provides functionality to sign up a client for free using the provided organization name and email.
    """
    def action(self, organization_name: str, email: str) -> SignupReponseCredentials:
        """
        Executes the free signup action with the given parameters.

        Args:
            organization_name (str): The name of the organization.
            email (str): The email address for signup.

        Returns:
            SignupReponseCredentials: The response containing the signup credentials.
        """
