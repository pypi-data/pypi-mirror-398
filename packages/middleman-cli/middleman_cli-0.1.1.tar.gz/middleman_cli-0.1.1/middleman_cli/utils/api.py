"""API client for Middleman."""

from pathlib import Path
from typing import Any, Optional

import httpx
import yaml
from rich.console import Console

console = Console()

DEFAULT_API_URL = "https://api.middleman.run/api/v1"
CONFIG_DIR = Path.home() / ".middleman"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class ConfigError(Exception):
    """Configuration error."""
    pass


class APIError(Exception):
    """API request error."""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    CONFIG_FILE.chmod(0o600)  # Secure permissions


def get_api_key() -> str:
    """Get API key from config."""
    config = get_config()
    api_key = config.get("api_key")
    if not api_key:
        raise ConfigError(
            "Not authenticated. Run 'middleman login' first."
        )
    return api_key


def get_api_url() -> str:
    """Get API URL from config or default."""
    config = get_config()
    return config.get("api_url", DEFAULT_API_URL)


class MiddlemanClient:
    """HTTP client for Middleman API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_url = get_api_url()
        self.api_key = api_key or get_api_key()
        self.client = httpx.Client(
            base_url=self.api_url,
            headers={"X-API-Key": self.api_key},
            timeout=30.0,
        )

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response."""
        if response.status_code == 401:
            raise APIError("Invalid API key. Run 'middleman login' to re-authenticate.", 401)

        if response.status_code == 403:
            raise APIError("Permission denied.", 403)

        if response.status_code == 404:
            raise APIError("Resource not found.", 404)

        if response.status_code >= 400:
            try:
                error = response.json()
                message = error.get("error", {}).get("message", response.text)
            except Exception:
                message = response.text
            raise APIError(message, response.status_code)

        return response.json()

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make GET request."""
        response = self.client.get(path, params=params)
        return self._handle_response(response)

    def post(self, path: str, json: Optional[dict] = None) -> dict:
        """Make POST request."""
        response = self.client.post(path, json=json)
        return self._handle_response(response)

    def delete(self, path: str) -> dict:
        """Make DELETE request."""
        response = self.client.delete(path)
        return self._handle_response(response)

    def patch(self, path: str, json: Optional[dict] = None) -> dict:
        """Make PATCH request."""
        response = self.client.patch(path, json=json)
        return self._handle_response(response)

    # Convenience methods
    def get_user(self) -> dict:
        """Get current user info."""
        return self.get("/users/me")

    def get_balance(self) -> dict:
        """Get credit balance."""
        return self.get("/billing/balance")

    def list_jobs(self, limit: int = 20, status: Optional[str] = None) -> dict:
        """List jobs."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        return self.get("/jobs", params=params)

    def get_job(self, job_id: str) -> dict:
        """Get job details."""
        return self.get(f"/jobs/{job_id}")

    def create_job(self, job_config: dict) -> dict:
        """Create a new job."""
        return self.post("/jobs", json=job_config)

    def cancel_job(self, job_id: str) -> dict:
        """Cancel a job."""
        return self.post(f"/jobs/{job_id}/cancel")

    def get_job_logs(self, job_id: str, tail: int = 100) -> dict:
        """Get job logs."""
        return self.get(f"/jobs/{job_id}/logs", params={"tail": tail})

    def close(self):
        """Close the client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
