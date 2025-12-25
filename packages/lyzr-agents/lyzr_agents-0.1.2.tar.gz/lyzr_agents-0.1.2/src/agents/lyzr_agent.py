import uuid
from typing import Optional
from dataclasses import dataclass

import requests


LYZR_API_BASE_URL = "https://agent-prod.studio.lyzr.ai/v3"


@dataclass
class LyzrResponse:
    """Response from Lyzr API."""

    response: str
    raw: Optional[dict] = None


class LyzrAgent:
    """Executor for Lyzr agents via API."""

    def __init__(self, api_key: str, user_id: str):
        self.api_key = api_key
        self.user_id = user_id
        self.base_url = LYZR_API_BASE_URL

    def execute(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> LyzrResponse:
        """Execute a Lyzr agent with the given message.

        Args:
            agent_id: The ID of the agent to execute.
            message: The message to send to the agent.
            session_id: Optional session ID. Generated if not provided.

        Returns:
            LyzrResponse containing the agent's response.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        if session_id is None:
            session_id = f"{agent_id}-{uuid.uuid4().hex[:12]}"

        url = f"{self.base_url}/inference/chat/"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        payload = {
            "user_id": self.user_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "message": message,
        }

        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        response_text = data.get("response", "")

        return LyzrResponse(response=response_text, raw=data)
