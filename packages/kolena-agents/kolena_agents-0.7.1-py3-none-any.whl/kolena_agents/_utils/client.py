from importlib.metadata import version
from typing import Optional

from kolena_agents._generated.openapi_client import ApiClient  # type: ignore
from kolena_agents._generated.openapi_client import Configuration  # type: ignore
from kolena_agents._resources.access_logs import AccessLogs
from kolena_agents._resources.agent import Agent
from kolena_agents._resources.agent_run import AgentRun
from kolena_agents._utils.config import get_api_key
from kolena_agents._utils.config import get_host

VERSION = version("kolena-agents")


def _get_client(
    api_key: Optional[str] = None,
    host: Optional[str] = None,
) -> ApiClient:
    if api_key is None:
        api_key = get_api_key()
    if host is None:
        host = get_host()

    if api_key is None:
        raise ValueError("No API token provided")

    configuration = Configuration(
        host=host,
        access_token=api_key,
    )
    client = ApiClient(configuration)
    client.user_agent = f"kolena-agents-python-{VERSION}"
    return client


class Client:
    """Main client class for interacting with the Kolena Agents API."""

    access_logs: AccessLogs
    agent_run: AgentRun

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
    ) -> None:
        """Initialize the Kolena Agents client.

        Args:
            api_key: Optional API key. If not provided, will attempt to load from environment.
            host: Optional API host. If not provided, will use default host.
        """
        self._client = _get_client(api_key=api_key, host=host)
        self.access_logs = AccessLogs(self._client)
        self.agent_run = AgentRun(self._client)
        self.agent = Agent(self._client)
