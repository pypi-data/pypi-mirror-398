from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel

class RemoveUserRequest(BaseRequestModel):
    """Request model for removing users from Copilot subscription."""
    selected_usernames: list[str]
