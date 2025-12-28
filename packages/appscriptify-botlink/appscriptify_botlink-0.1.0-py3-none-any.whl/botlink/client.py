import os
import requests

AS_SERVER_URL = "https://botlink.appscriptify.com"
DEFAULT_TIMEOUT = 20


# ============================
# Project (lazy-loaded object)
# ============================
class Project:
    def __init__(self, client, project_id):
        self._client = client
        self.project_id = project_id

        def _get_info(self):
            resp = requests.post(
                f"{AS_SERVER_URL}/api/sdk/project/info",
                json={
                    "api_key": self._client.api_key,
                    "project_id": self.project_id,
                },
                timeout=DEFAULT_TIMEOUT,
            )
            if not resp.ok:
                raise RuntimeError(
                    f"Failed to fetch project info ({resp.status_code})"
                )
            return resp.json()
        
        project_info = _get_info(self)
        self.name = project_info.get("project_name")
        self.as_key = project_info.get("as_key")
        self.authorised_domains = project_info.get("authorised_domain", None)
        self.agent = Agent(self.project_id, self._client)


    
    # Should print ALL project info as a dict, The info should be under double quotes
    def __repr__(self):
        return f'Botlink.Project({{project_id: "{self.project_id}", name: "{self.name}", as_key: "{self.as_key}", authorised_domains: "{self.authorised_domains}"}})'

    def greet(self):
        return f"Hello from project {self.project_id}"

    # future expansion
    # def settings(self):
    # def logs(self):
    # def delete(self):
    # ...


# ============================
# Lazy Project Registry
# ============================
class ProjectRegistry:
    def __init__(self, client, project_ids):
        self._client = client
        self._project_ids = list(project_ids)
        self._instances = {}

    def __getitem__(self, project_id) -> Project:
        if project_id not in self._project_ids:
            raise KeyError(f"Project '{project_id}' not found")

        if project_id not in self._instances:
            self._instances[project_id] = Project(self._client, project_id)

        return self._instances[project_id]

    def list(self):
        return self._project_ids

    def __contains__(self, project_id):
        return project_id in self._project_ids

    def __repr__(self):
        return repr(self._project_ids)
    
    def __len__(self):
        return len(self._project_ids)

    __str__ = __repr__



# ============================
# Botlink Client (ENTRY POINT)
# ============================
class Botlink:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("BOTLINK_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "via BOTLINK_API_KEY environment variable"
            )

        # validate + fetch metadata
        projects = self._validate_api_key()
        
        # lazy-loaded projects
        self.projects = ProjectRegistry(self, projects)

    def _validate_api_key(self) -> list[str]:
        response = requests.post(
            f"{AS_SERVER_URL}/api/sdk/validate/key",
            json={"api_key": self.api_key},
            timeout=10,
        )

        if not response.ok:
            raise RuntimeError(
                f"API key validation failed ({response.status_code})"
            )

        data = response.json()

        if not data.get("valid"):
            raise ValueError(f"Invalid API key: {data.get('reason')}")

        return data.get("projects", [])

class Agent:
    def __init__(self, project_id, client):
        self.project_id = project_id
        self.client = client

        def _get_agent_info(self):
            resp = requests.post(
                f"{AS_SERVER_URL}/api/sdk/agent/info",
                json={
                    "api_key": client.api_key,
                    "project_id": self.project_id,
                },
                timeout=DEFAULT_TIMEOUT,
            )
            if not resp.ok:
                raise RuntimeError(
                    f"Failed to fetch agent info ({resp.status_code})"
                )
            return resp.json()


        agent_info = _get_agent_info(self)

        self.bot_name = agent_info.get("bot_name")
        self.bot_description = agent_info.get("bot_description")
        self.instructions = agent_info.get("instructions")
        self.temperature = agent_info.get("temperature")
        self.welcome_message = agent_info.get("welcome_message")

    def chat(self, message: str, history: list = None, temperature: float = None, instructions: str = None, max_tokens: int = None) -> dict:
        resp = requests.post(
            f"{AS_SERVER_URL}/api/sdk/agent/chat",
            json={
                "api_key": self.client.api_key,
                "project_id": self.project_id,
                "message": message,
                "history": history,
                "temperature": temperature,
                "instructions": instructions,
                "max_tokens": max_tokens,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if not resp.ok:
            raise RuntimeError(
                f"Failed to chat with agent ({resp.status_code})"
            )
        return resp.json()
            

    def __repr__(self):
        return f'Botlink.Agent({{project_id: "{self.project_id}", bot_name: "{self.bot_name}", bot_description: "{self.bot_description}", instructions: "{self.instructions}", temperature: "{self.temperature}", welcome_message: "{self.welcome_message}"}})'
    
    
    