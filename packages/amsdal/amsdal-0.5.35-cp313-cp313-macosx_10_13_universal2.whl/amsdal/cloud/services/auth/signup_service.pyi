from _typeshed import Incomplete
from amsdal.cloud.services.actions.signup_action import FreeSignupAction as FreeSignupAction
from amsdal.configs.main import settings as settings

LICENCE_PATH: Incomplete
LICENCE_MESSAGE: Incomplete

def _input(msg: str) -> str: ...
def _print(msg: str) -> None: ...
def want_signup_input() -> str: ...
def licence_input() -> str: ...
def organization_name_input() -> str: ...
def email_input() -> str: ...

class SignupService:
    """
    Service to handle the signup process for the Amsdal Framework.

    This class provides functionality to prompt the user for signup details, validate the license agreement,
    and create credentials for the user.
    """
    @classmethod
    def signup_prompt(cls) -> bool:
        """
        Prompts the user to sign up for the Amsdal Framework.

        This method guides the user through the signup process, including accepting the license agreement and
        entering organization and email details. It then creates credentials for the user.

        Returns:
            bool: True if the signup process is completed successfully, False otherwise.
        """
