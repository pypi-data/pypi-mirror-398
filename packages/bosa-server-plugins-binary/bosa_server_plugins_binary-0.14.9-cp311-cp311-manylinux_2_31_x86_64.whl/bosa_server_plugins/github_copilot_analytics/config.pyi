from pydantic import BaseModel

class GithubCopilotAnalyticsConfig(BaseModel):
    """Configuration for GitHub Copilot Analytics integration.
    
    Attributes:
        github_token (str): GitHub Personal Access Token with manage_billing:copilot or read:org scope.
        organization (str): GitHub organization name.
    """
    github_token: str
    organization: str
