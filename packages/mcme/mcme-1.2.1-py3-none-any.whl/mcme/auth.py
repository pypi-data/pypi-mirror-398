from keycloak import KeycloakOpenID, exceptions
import click


class Authenticator:
    def __init__(self, auth_config: dict) -> None:
        """Load state from a local file"""
        self.keycloak_openid = KeycloakOpenID(
            server_url=auth_config["server_url"],
            client_id=auth_config["client_id"],
            realm_name=auth_config["realm_name"],
        )

    def get_user_from_token(self, token: str) -> str:
        try:
            userinfo = self.keycloak_openid.userinfo(token)
        except exceptions.KeycloakAuthenticationError:
            raise click.ClickException("Token is invalid.")
        return userinfo.get("preferred_username")

    def is_access_token_valid(self, token: str) -> bool:
        """Validate the access token on keyloak"""
        try:
            self.keycloak_openid.userinfo(token)
            return True
        except exceptions.KeycloakAuthenticationError:
            return False

    def authenticate(self, username: str, password: str) -> str:
        """Get keycloak access token by authenticating using username and password"""
        if username is None:
            username = click.prompt("Username", type=str)
        if password is None:
            password = click.prompt("Password", type=str, hide_input=True)
        generated_tokens = self.keycloak_openid.token(username, password)
        return generated_tokens
