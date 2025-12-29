"""Module for custom authentication"""

import json
import os
import sys
from datetime import datetime, timezone
import requests
from dateutil.parser import parse
from requests.auth import AuthBase
import logging

class RefreshToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, access_key, secret_key):
        self.bearer_token = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.VALIDATE_ACCESS_KEY_URL = (
            f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai/v1/accounting/validate_access_key"
        )

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        if self.bearer_token is None:
            raise ValueError(
                "Failed to obtain refresh token. Cannot authenticate request. "
                "Please check your access_key and secret_key credentials."
            )
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain a bearer token using the provided access key and secret key."""
        payload_dict = {
            "accessKey": self.access_key,
            "secretKey": self.secret_key,
        }
        payload = json.dumps(payload_dict)
        headers = {"Content-Type": "text/plain"}
        response = None
        try:
            response = requests.request(
                "GET",
                self.VALIDATE_ACCESS_KEY_URL,
                headers=headers,
                data=payload,
                timeout=120,
            )
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=e,
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if not response or response.status_code != 200:
            error_msg = f"Error response from the auth server in RefreshToken (status: {getattr(response, 'status_code', 'unknown')}): {getattr(response, 'text', 'No response text')}"
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        try:
            res_dict = response.json()
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=Exception(f"Invalid JSON in RefreshToken response: {str(e)}"),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("refreshToken"):
            logging.debug(f"res_dict: {res_dict}")
            self.bearer_token = "Bearer " + res_dict["data"]["refreshToken"]
        else:
            error_msg = f"The provided credentials are incorrect in RefreshToken. Response: {res_dict}"
            logging.error(error_msg)
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )


class AuthToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(
        self,
        access_key,
        secret_key,
        refresh_token,
    ):
        self.bearer_token = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.refresh_token = refresh_token
        self.expiry_time = datetime.now(timezone.utc)
        self.REFRESH_TOKEN_URL = (
            f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai/v1/accounting/refresh"
        )

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        if self.bearer_token is None:
            raise ValueError(
                "Failed to obtain authentication token. Cannot authenticate request. "
                "This may be due to invalid credentials or server issues."
            )
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain an authentication bearer token using the provided refresh token."""
        # Ensure refresh token is obtained first
        if self.refresh_token.bearer_token is None:
            try:
                self.refresh_token.set_bearer_token()
            except Exception as e:
                error_msg = f"Failed to obtain refresh token before getting auth token: {e}"
                logging.error(error_msg)
                raise RuntimeError(error_msg) from e

        # Use the refresh token bearer_token as an authorization header
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.refresh_token.bearer_token
        }
        response = None
        try:
            response = requests.request(
                "POST",
                self.REFRESH_TOKEN_URL,
                headers=headers,
                timeout=120,
            )
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=e,
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if not response or response.status_code != 200:
            error_msg = f"Error response from the auth server in AuthToken (status: {getattr(response, 'status_code', 'unknown')}): {getattr(response, 'text', 'No response text')}"
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        try:
            res_dict = response.json()
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=Exception(f"Invalid JSON in AuthToken response: {str(e)}"),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("token"):
            self.bearer_token = "Bearer " + res_dict["data"]["token"]
            self.expiry_time = parse(res_dict["data"]["expiresAt"])
        else:
            error_msg = f"The provided credentials are incorrect in AuthToken. Response: {res_dict}"
            logging.error(error_msg)
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
