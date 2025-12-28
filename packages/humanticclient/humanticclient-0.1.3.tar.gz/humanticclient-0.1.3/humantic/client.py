import os
import time
from typing import Any

from dotenv import load_dotenv
import httpx

load_dotenv()


class HumanticClient:
    """Simple client for Humantic AI API."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.humantic.ai/v1") -> None:
        """
        Initialize the Humantic AI client.

        Args:
            api_key: Humantic AI API key. If None, reads from HUMANTIC_API_KEY env var (.env supported).
            base_url: Base URL for the API.
        """
        self.api_key = api_key or os.environ.get("HUMANTIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set via HUMANTIC_API_KEY environment variable")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def create_profile(self, user_id: str) -> dict[str, Any]:
        """
        Create a new profile analysis.

        Args:
            user_id: LinkedIn profile URL or any unique identifier.

        Returns:
            Response dict with analysis status.
        """
        url = f"{self.base_url}/user-profile/create"
        params = {"apikey": self.api_key, "id": user_id}
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_profile(self, user_id: str, persona: str = "sales") -> dict[str, Any]:
        """
        Fetch an existing profile analysis.

        Args:
            user_id: LinkedIn profile URL or unique identifier used during creation.
            persona: Persona for the analysis. Default is "sales".

        Returns:
            Profile analysis results.

        Raises:
            httpx.HTTPStatusError: If profile not found or other API error.
        """
        url = f"{self.base_url}/user-profile"
        params = {"apikey": self.api_key, "id": user_id, "persona": persona}
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_or_create_profile(self, user_id: str, persona: str = "sales", max_wait: int = 60) -> dict[str, Any]:
        """
        Fetch a profile, creating it if it doesn't exist.

        Args:
            user_id: LinkedIn profile URL or unique identifier.
            persona: Persona for the analysis. Default is "sales".
            max_wait: Maximum seconds to wait for analysis completion.

        Returns:
            Profile analysis results.
        """
        result = self.fetch_profile(user_id, persona=persona)

        # Check if profile needs to be created (API returns 200 with status_code 444)
        if result.get("metadata", {}).get("status_code") == 444:
            self.create_profile(user_id)
            # Poll until analysis is complete
            for _ in range(max_wait):
                time.sleep(1)
                result = self.fetch_profile(user_id, persona=persona)
                if result.get("metadata", {}).get("analysis_status") == "COMPLETE":
                    break

        return result

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HumanticClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
