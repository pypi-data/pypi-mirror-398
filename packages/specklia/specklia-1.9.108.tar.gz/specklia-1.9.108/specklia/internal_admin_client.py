"""Specklia internal admin client module."""

import logging
from typing import Callable, Literal, Self

import pandas as pd
import requests

_log = logging.getLogger(__name__)


class SpeckliaInternalAdminClient:
    """Specklia client for endpoints only accessible to internal Specklia administrators.

    Parameters
    ----------
    specklia_request : Callable
        The function to use to make requests to Specklia internal admin endpoints.
    """

    def __init__(
        self: Self,
        specklia_request: Callable,
    ) -> None:
        self._specklia_request = specklia_request

    def _request(
        self: Self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
        data: str | None = None,
    ) -> requests.Response:
        return self._specklia_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json,
            data=data,
        )

    def list_all_groups(self: Self) -> pd.DataFrame:
        """
        List all groups.

        Returns
        -------
        pd.DataFrame
            A dataframe describing all groups
        """
        response = self._request("GET", "groups")
        _log.info("listing all groups within Specklia.")
        return pd.DataFrame(response.json()).convert_dtypes()

    def generate_user_api_key(self: Self, user_id: str) -> dict[str, str]:
        """
        Generate an API key for a user, creating the user if they do not already exist.

        This will create the user if they do not already exist, and will replace any existing API key if present.

        Parameters
        ----------
        user_id : str
            The ID of the user to generate an API key for.

        Returns
        -------
        dict[str, str]
            A dictionary containing the `user_id` and the generated `token`.
        """
        response = self._request("PUT", "generate_user_api_key/" + user_id)
        _log.info("Generated API key for user ID %s.", user_id)
        return response.json()
