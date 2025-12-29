import requests

from decube_auth.config import DEFAULT_BASE_URL
from decube_auth.exceptions import (
    AuthenticationError,
    ConflictError,
    BadRequestError,
    ServerError,
)


class AuthClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _handle_response(self, response):
        if response.status_code in (200, 201):
            return response.json()

        if response.status_code == 400:
            raise BadRequestError(response.json())

        if response.status_code == 401:
            raise AuthenticationError(response.json())

        if response.status_code == 409:
            raise ConflictError(response.json())

        raise ServerError(
            f"Unexpected error ({response.status_code}): {response.text}"
        )

    def signup(self, email: str, password: str):
        resp = requests.post(
            f"{self.base_url}/auth/signup",
            headers=self._headers(),
            json={"email": email, "password": password},
            timeout=5,
        )
        return self._handle_response(resp)

    def login(self, email: str, password: str):
        resp = requests.post(
            f"{self.base_url}/auth/login",
            headers=self._headers(),
            json={"email": email, "password": password},
            timeout=5,
        )
        return self._handle_response(resp)

    def refresh(self, refresh_token: str):
        resp = requests.post(
            f"{self.base_url}/auth/refresh",
            headers=self._headers(),
            json={"refresh_token": refresh_token},
            timeout=5,
        )
        return self._handle_response(resp)
