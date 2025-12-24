from mcme.helpers import create_parent_dir_if_not_exists

import json
import os


class State:
    """Class for storing an app state that is in sync with a local state file."""

    def __init__(self, keycloak_file: str) -> None:
        """Load state from a local file"""
        self.keycloak_file: str = keycloak_file
        self._active_user = None
        self._user_keycloak_tokens = {}
        if not os.path.exists(self.keycloak_file):
            return
        with open(self.keycloak_file) as state:
            state_json = json.load(state)
            self._active_user = state_json.get("active_user")
            self._user_keycloak_tokens = state_json.get("keycloak_tokens")

    @property
    def active_user(self):
        return self._active_user

    @active_user.setter
    def active_user(self, username):
        """Sets active user and syncs the local state file."""
        self._active_user = username
        self.update_local_file()

    @property
    def active_access_token(self) -> str | None:
        if (keycloak_tokens := self._user_keycloak_tokens.get(self.active_user)) is not None:
            return keycloak_tokens.get("access_token")
        return None

    @active_access_token.setter
    def active_access_token(self, access_token) -> None:
        """Sets a new access token for the active user and syncs the local state file."""
        self._user_keycloak_tokens[self.active_user] = {"access_token": access_token}
        self.update_local_file()

    def set_active_keycloak_token(self, keycloak_token) -> None:
        """Sets new keycloak tokens for the active user and syncs the local state file."""
        self._user_keycloak_tokens[self.active_user] = keycloak_token
        self.update_local_file()

    def update_local_file(self) -> None:
        """Save current state to local file"""
        create_parent_dir_if_not_exists(self.keycloak_file)
        with open(self.keycloak_file, "w") as state_file:
            json.dump(self.to_dict(), state_file)

    def to_dict(self) -> dict:
        return {"active_user": self._active_user, "keycloak_tokens": self._user_keycloak_tokens}
