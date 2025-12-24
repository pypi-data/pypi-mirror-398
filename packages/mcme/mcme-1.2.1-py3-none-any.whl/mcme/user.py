import click
from .logger import log
from dataclasses import dataclass


@dataclass
class User:
    email: str
    credits: int


def request_user_info(user_api_instance) -> User:
    """
    Call API for info about current user.
    """
    try:
        api_response_user = user_api_instance.describe_user()
        if api_response_user.data is None or api_response_user.data.attributes is None:
            raise click.ClickException("User info response came back empty")
        return User(email=api_response_user.data.attributes.email, credits=api_response_user.data.attributes.credits)
    except Exception as e:
        log.info("Exception when calling UserApi->describe_user: %s\n" % e)

    return User(email="", credits=0)
