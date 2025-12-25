"""
MQTT-based database subscriber implementations.

This module provides database subscriber classes that interact with
MQTT-based dispatcher services.
"""
import logging
from datetime import datetime

from requests import HTTPError

from .base import DbSubscriberBase

logger = logging.getLogger(__name__)

__all__ = ["DbSubscriber", "Ctxt", "Db41", "Db44"]


class DbSubscriber(DbSubscriberBase):
    """
    Database subscriber for MQTT-based dispatcher services.

    This class provides methods for querying resources through an
    MQTT dispatcher API.
    """

    @property
    def columns(self) -> list:
        """
        List columns for a resource.

        Returns
        -------
        list
            List of columns keyed by table name.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        response = self.auth.get(f"resources/{self._label}/columns")
        response.raise_for_status()
        try:
            return response.json()["Messages"]
        except KeyError:
            raise HTTPError("Invalid resource payload structure. Expected 'Messages'.")

    def keywords(
        self,
        *,
        columns: str | list[str] | None = None,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list]:
        """
        Check the keywords being provided.

        Parameters
        ----------
        columns : str or list[str], optional
            Column name or list of column names.
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
        dict
            Dictionary of keywords.

        Raises
        ------
        requests.HTTPError
            If the request fails.
        """
        params = self._build_query_params(
            columns=columns,
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(f"keywords{params}")
        response.raise_for_status()
        return response.json()

    def distinct(
        self,
        columns: str | list[str],
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list]:
        """
        Get distinct values for a column.

        Parameters
        ----------
        columns : str or list[str]
            Column name or list of column names.
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of distinct values to return.

        Returns
        -------
        dict
            Dictionary of distinct values keyed by column name.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        columns_str = self._normalize_columns(columns)
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(
            f"resources/{self._label}/distinct/{columns_str}{params}"
        )
        response.raise_for_status()
        return response.json()

    def count(
        self,
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
    ) -> int:
        """
        Get the count of records.

        Parameters
        ----------
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.

        Returns
        -------
        int
            The count of rows.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
        )
        response = self.auth.get(f"resources/{self._label}/count{params}")
        response.raise_for_status()
        try:
            return response.json()[0][0]
        except (IndexError, TypeError):
            raise HTTPError("Invalid resource response.")

    def list(
        self,
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """
        Get the records.

        Parameters
        ----------
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        list
            List of strings representing the records.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(f"resources/{self._label}/list{params}")
        response.raise_for_status()
        return response.json()


class Ctxt(DbSubscriber):
    """Subscriber for ctxt database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "ctxt"


class Db41(DbSubscriber):
    """Subscriber for db41 database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "db41"


class Db44(DbSubscriber):
    """Subscriber for db44 database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "db44"
