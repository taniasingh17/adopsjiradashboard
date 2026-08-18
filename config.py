import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    jira_url: str
    jira_email: str
    jira_api_token: str


def load_config() -> Config:
    missing = []
    jira_url = os.getenv("JIRA_URL", "")
    jira_email = os.getenv("JIRA_EMAIL", "")
    jira_api_token = os.getenv("JIRA_API_TOKEN", "")

    if not jira_url:
        missing.append("JIRA_URL")
    if not jira_email:
        missing.append("JIRA_EMAIL")
    if not jira_api_token:
        missing.append("JIRA_API_TOKEN")

    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        jira_url=jira_url,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
    )
