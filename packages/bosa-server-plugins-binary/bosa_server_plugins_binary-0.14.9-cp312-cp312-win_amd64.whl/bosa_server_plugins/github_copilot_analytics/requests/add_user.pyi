from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel

class AddUserRequest(BaseRequestModel):
    """Request model for adding users to Copilot subscription."""
    selected_usernames: list[str]
