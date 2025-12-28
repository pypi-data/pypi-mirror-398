import base64
from dataclasses import dataclass
from typing import Optional, Any

import requests


@dataclass
class SupportAgentQuery:
    message: str
    session_id: Optional[str] = None


class SupportAgent:
    def __init__(self, user_id: str, api_key: str) -> None:
        self.user_id = user_id
        self.api_key = api_key

    def query(self, params: SupportAgentQuery) -> Any:
        """
        Synchronous version of the TypeScript `query` method.
        Returns the `requests.Response` object.
        """
        # Prepare multipart form fields
        data = {"message": params.message}
        if params.session_id:
            data["session_id"] = params.session_id

        # Build Basic auth token: base64("userId:apiKey")
        token_bytes = f"{self.user_id}:{self.api_key}".encode("utf-8")
        auth_token = base64.b64encode(token_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_token}",
        }

        response = requests.post(
            "https://api.bizagenthub.ai/support-agent",
            headers=headers,
            data=data
        )
        return response