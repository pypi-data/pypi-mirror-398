# Kolena Agents

Python client for interacting with Kolena Agents.

## Initialization

An API Key is required to use the python client.
Generate a key from your user profile within the [Kolena web UI](https://agents.kolena.com).

Copy the created key and store in a `KOLENA_API_KEY` environment variable:

```shell
export KOLENA_API_KEY="your-api-key"
```

## Usage

Here's an example of how to use the client to add, download, list, and delete agent runs:

```python
from kolena_agents import Client

client = Client()

# add new agent run
new_run = client.agent_run.add(agent_id=1, files=["path/to/file1", "path/to/file2"])

# download agent run
run = client.agent_run.get(agent_id=1, run_id=2)

# alternatively, list all agent runs
all_runs = client.agent_run.list(agent_id=1)

# delete agent run
client.agent_run.delete(agent_id=1, run_id=2)

# list all agents
all_agents = client.agent.list()

# get an agent
agent = client.agent.get(agent_id=1)
```

## Webhook

Kolena provides a helper function to handle signature verification and parsing. See [Webhook Integration](https://docs.agents.kolena.com/connections#webhook) for more information.

```python
from kolena_agents import webhook

result = webhook.construct_event(request_body, secret, request_headers)
```

## Supported Python Versions

Python versions 3.8 and later are supported.
