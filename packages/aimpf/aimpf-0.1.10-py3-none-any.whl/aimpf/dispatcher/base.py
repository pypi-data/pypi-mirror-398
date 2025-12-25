"""
Base classes for database subscribers.

This module provides common functionality shared between MQTT and MySQL
database subscriber implementations.
"""
import logging
from datetime import datetime

import requests

from .dispatcher import Dispatcher

logger = logging.getLogger(__name__)

__all__ = ["DbSubscriberBase"]


class DbSubscriberBase(Dispatcher):
    """
    Base class for database subscribers.

    This class provides common functionality shared between different
    database subscriber implementations (MQTT, MySQL, etc.).
    """

    # Error message constant for label validation
    _LABEL_NOT_SET_ERROR = "Label is not set"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label: str | None = None

    @property
    def label(self) -> str | None:
        """
        The label of the resource.
        """
        return self._label

    def _require_label(self) -> None:
        """
        Validate that the label is set.

        Raises
        ------
        ValueError
            If the label is not set.
        """
        if self._label is None:
            raise ValueError(self._LABEL_NOT_SET_ERROR)

    @staticmethod
    def _build_query_params(
        *,
        columns: str | list[str] | None = None,
        database: str | None = None,
        table: str | None = None,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> str:
        """
        Build a query parameter string from the provided arguments.

        Parameters
        ----------
        columns : str or list[str], optional
            Column name or list of column names.
        database : str, optional
            Database name (MySQL only).
        table : str, optional
            Table name (MySQL only).
        where : str, optional
            Comma-separated list of conditions.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        str
            Query parameter string starting with '?' if any parameters exist,
            empty string otherwise.
        """
        param_list = []

        if columns:
            columns_str = (
                ",".join(columns) if isinstance(columns, list) else columns
            )
            param_list.append(f"columns={columns_str}")
        if database:
            param_list.append(f"database={database}")
        if table:
            param_list.append(f"table={table}")
        if where:
            param_list.append(f"where={where}")
        if start:
            param_list.append(f"from={start}")
        if end:
            param_list.append(f"to={end}")
        if limit is not None:
            param_list.append(f"limit={int(limit)}")

        return "?" + "&".join(param_list) if param_list else ""

    @staticmethod
    def _normalize_columns(columns: str | list[str]) -> str:
        """
        Normalize columns parameter to a comma-separated string.

        Parameters
        ----------
        columns : str or list[str]
            Column name or list of column names.

        Returns
        -------
        str
            Comma-separated column string.
        """
        if isinstance(columns, list):
            return ",".join(columns)
        return columns

    def check(self) -> requests.Response:
        """
        Check the health of the server.

        Returns
        -------
        requests.Response
            The response object.
        """
        return self.auth.get("check")

    def is_alive(self) -> bool:
        """
        Verify that the server is running and accepting API requests.

        Returns
        -------
        bool
            True if the server is running, False otherwise.
        """
        try:
            response = self.check()
            response.raise_for_status()
            return response.json()["health"] == "alive"
        except KeyError:
            logger.error("Invalid health check response structure.")
            return False
        except Exception as e:
            logger.error("Error checking %s: %s", self.label, e)
            return False

    def list_resources(self) -> dict:
        """
        List resources available.

        Returns
        -------
        dict
            Dictionary of available resources.

        Raises
        ------
        requests.HTTPError
            If the request fails.
        """
        response = self.auth.get("resources/list")
        response.raise_for_status()
        return response.json()
